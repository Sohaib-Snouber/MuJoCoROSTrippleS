from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue, ParameterFile
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    mujoco_namespace = "mujoco"
    controller_manager = "/mujoco/controller_manager"

    xacro_file = PathJoinSubstitution([
        FindPackageShare("ur5e_mujoco_sim"),
        "urdf",
        "ur5e.urdf.xacro",
    ])

    controllers_file = PathJoinSubstitution([
        FindPackageShare("ur5e_mujoco_sim"),
        "config",
        "controllers.yaml",
    ])

    robot_description = ParameterValue(
        Command([
            FindExecutable(name="xacro"),
            " ",
            xacro_file,
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=mujoco_namespace,
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,
            }
        ],
        remappings=[
            ("/tf", "/mujoco/tf"),
            ("/tf_static", "/mujoco/tf_static"),
        ],
    )

    control_node = Node(
        package="mujoco_ros2_control",
        executable="ros2_control_node",
        namespace=mujoco_namespace,
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
            },
            ParameterFile(
                controllers_file,
                allow_substs=True,
            ),
        ],
        remappings=[
            ("/mujoco_actuators_states", "/mujoco/actuator_states"),
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            controller_manager,
            "--param-file",
            controllers_file,
            "--controller-ros-args",
            "--ros-args "
            "--remap /joint_states:=/mujoco/joint_states "
            "--remap /dynamic_joint_states:=/mujoco/dynamic_joint_states",
        ],
    )

    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            controller_manager,
            "--param-file",
            controllers_file,
        ],
    )

    return LaunchDescription([
        robot_state_publisher,
        control_node,
        joint_state_broadcaster_spawner,
        joint_trajectory_controller_spawner,
    ])

