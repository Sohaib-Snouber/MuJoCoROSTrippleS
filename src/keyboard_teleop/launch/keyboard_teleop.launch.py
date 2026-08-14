from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    output_topic = LaunchConfiguration("output_topic")
    linear_speed = LaunchConfiguration("linear_speed")
    angular_speed = LaunchConfiguration("angular_speed")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument(
            "output_topic",
            default_value="cmd_vel",
            description="TwistStamped output topic",
        ),

        DeclareLaunchArgument(
            "linear_speed",
            default_value="0.50",
            description="Linear velocity in m/s",
        ),

        DeclareLaunchArgument(
            "angular_speed",
            default_value="0.90",
            description="Angular velocity in rad/s",
        ),

        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use ROS simulation time",
        ),

        Node(
            package="keyboard_teleop",
            executable="keyboard_teleop_node",
            name="keyboard_teleop",
            output="screen",
            parameters=[{
                "output_topic": output_topic,
                "linear_speed": ParameterValue(
                    linear_speed,
                    value_type=float,
                ),
                "angular_speed": ParameterValue(
                    angular_speed,
                    value_type=float,
                ),
                "use_sim_time": ParameterValue(
                    use_sim_time,
                    value_type=bool,
                ),
            }],
        ),
    ])

