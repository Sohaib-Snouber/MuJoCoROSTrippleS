#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#include "geometry_msgs/msg/twist_stamped.hpp"
#include "rclcpp/rclcpp.hpp"


class TerminalGuard
{
public:
  TerminalGuard()
  {
    terminal_fd_ = open("/dev/tty", O_RDWR);

    if (terminal_fd_ == -1) {
      throw std::runtime_error(
        std::string("Failed to open /dev/tty: ") +
        std::strerror(errno));
    }

    if (tcgetattr(terminal_fd_, &original_settings_) == -1) {
      const int error_number = errno;

      close(terminal_fd_);
      terminal_fd_ = -1;

      throw std::runtime_error(
        std::string("Failed to read terminal settings: ") +
        std::strerror(error_number));
    }

    termios raw_settings = original_settings_;

    raw_settings.c_lflag &=
      static_cast<tcflag_t>(~(ICANON | ECHO));

    raw_settings.c_cc[VMIN] = 1;
    raw_settings.c_cc[VTIME] = 0;

    if (tcsetattr(
        terminal_fd_,
        TCSANOW,
        &raw_settings) == -1)
    {
      const int error_number = errno;

      close(terminal_fd_);
      terminal_fd_ = -1;

      throw std::runtime_error(
        std::string("Failed to configure terminal: ") +
        std::strerror(error_number));
    }
  }

  ~TerminalGuard()
  {
    if (terminal_fd_ != -1) {
      tcsetattr(
        terminal_fd_,
        TCSANOW,
        &original_settings_);

      close(terminal_fd_);
    }
  }

  TerminalGuard(const TerminalGuard &) = delete;
  TerminalGuard & operator=(const TerminalGuard &) = delete;

  int fd() const
  {
    return terminal_fd_;
  }

private:
  int terminal_fd_{-1};
  termios original_settings_{};
};


class KeyboardTeleopNode : public rclcpp::Node
{
public:
  KeyboardTeleopNode()
  : Node("keyboard_teleop")
  {
    output_topic_ =
      declare_parameter<std::string>(
        "output_topic",
        "cmd_vel");

    linear_speed_ =
      declare_parameter<double>(
        "linear_speed",
        0.10);

    angular_speed_ =
      declare_parameter<double>(
        "angular_speed",
        0.50);

    publisher_ =
      create_publisher<geometry_msgs::msg::TwistStamped>(
        output_topic_,
        rclcpp::SystemDefaultsQoS());

    printInstructions();
  }

  void run()
  {
    TerminalGuard terminal_guard;

    while (rclcpp::ok()) {
      char key = '\0';

      const ssize_t bytes_read =
        read(
          terminal_guard.fd(),
          &key,
          sizeof(key));

      if (bytes_read == -1) {
        if (errno == EINTR) {
          continue;
        }

        throw std::runtime_error(
          std::string("Failed to read keyboard input: ") +
          std::strerror(errno));
      }

      if (bytes_read == 0) {
        continue;
      }

      if (!handleKey(key)) {
        break;
      }
    }

    publishCommand(0.0, 0.0);
  }

private:
  bool handleKey(char key)
  {
    switch (key) {
      case 'w':
      case 'W':
        publishCommand(linear_speed_, 0.0);
        break;

      case 's':
      case 'S':
        publishCommand(-linear_speed_, 0.0);
        break;

      case 'a':
      case 'A':
        publishCommand(0.0, angular_speed_);
        break;

      case 'd':
      case 'D':
        publishCommand(0.0, -angular_speed_);
        break;

      case ' ':
      case 'x':
      case 'X':
        publishCommand(0.0, 0.0);
        break;

      case 'q':
      case 'Q':
        publishCommand(0.0, 0.0);
        return false;

      default:
        break;
    }

    return true;
  }

  void publishCommand(double linear_x, double angular_z)
  {
    geometry_msgs::msg::TwistStamped message;

    message.header.stamp = now();

    message.twist.linear.x = linear_x;
    message.twist.angular.z = angular_z;

    publisher_->publish(message);
  }

  void printInstructions() const
  {
    std::cout
      << "\nKeyboard teleoperation\n"
      << "----------------------\n"
      << "W : forward\n"
      << "S : backward\n"
      << "A : turn left\n"
      << "D : turn right\n"
      << "Space / X : stop\n"
      << "Q : quit\n\n"
      << "Output topic  : " << output_topic_ << "\n"
      << "Linear speed  : " << linear_speed_ << " m/s\n"
      << "Angular speed : " << angular_speed_ << " rad/s\n"
      << std::endl;
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr publisher_;

  std::string output_topic_;
  double linear_speed_;
  double angular_speed_;
};


int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  try {
    auto node = std::make_shared<KeyboardTeleopNode>();
    node->run();
  } catch (const std::exception & exception) {
    std::cerr
      << "Keyboard teleop failed: "
      << exception.what()
      << std::endl;

    rclcpp::shutdown();
    return 1;
  }

  rclcpp::shutdown();
  return 0;
}
