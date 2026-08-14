from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile, ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("turtlebot3_mujoco_sim")

    xacro_file = PathJoinSubstitution([
        package_share,
        "description",
        "turtlebot3_burger.urdf.xacro",
    ])

    controllers_file = PathJoinSubstitution([
        package_share,
        "config",
        "controllers.yaml",
    ])

    robot_description = {
        "robot_description": ParameterValue(
            Command([
                FindExecutable(name="xacro"),
                " ",
                xacro_file,
                " headless:=",
                LaunchConfiguration("headless"),
            ]),
            value_type=str,
        )
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ],
    )

    ros2_control_node = Node(
        package="mujoco_ros2_control",
        executable="ros2_control_node",
        output="both",
        emulate_tty=True,
        parameters=[
            {"use_sim_time": True},
            ParameterFile(controllers_file),
        ],
        on_exit=Shutdown(),
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--param-file",
            controllers_file,
        ],
        output="both",
    )

    diff_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "diff_drive_controller",
            "--param-file",
            controllers_file,
        ],
        output="both",
    )

    headless_argument = DeclareLaunchArgument(
        "headless",
        default_value="false",
        description="Run MuJoCo without the viewer",
    )

    return LaunchDescription([
        headless_argument,
        robot_state_publisher,
        ros2_control_node,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,
    ])
