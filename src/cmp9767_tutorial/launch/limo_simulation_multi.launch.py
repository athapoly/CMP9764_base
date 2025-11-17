import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # Constants for paths to different files and folders
    urdf_model_name = 'limo_four_diff.gazebo'
    world_file_name = 'simple.world'
    rviz_config_file_name = 'urdf.rviz'

    robot_name_in_model = 'limo_gazebosim'

    # Pose where we want to spawn the robots
    spawn_z_val = '0.0'

    ############ You do not need to change anything below this line #############

    # Set the path to different files and folders.
    pkg_gazebo_ros = FindPackageShare(package='gazebo_ros').find('gazebo_ros')

    default_urdf_model_path = os.path.join(
        get_package_share_directory('limo_description'),
        'urdf',
        urdf_model_name
    )

    world_path = os.path.join(
        get_package_share_directory('limo_gazebosim'),
        'worlds',
        world_file_name
    )

    gazebo_models_path = os.path.join(
        get_package_share_directory('limo_gazebosim'),
        'models'
    )
    os.environ["GAZEBO_MODEL_PATH"] = gazebo_models_path

    default_rviz_config_path = os.path.join(
        get_package_share_directory('limo_gazebosim'),
        'rviz',
        rviz_config_file_name
    )

    # Launch configuration variables specific to simulation
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gui = LaunchConfiguration('gui')
    headless = LaunchConfiguration('headless')
    namespace = LaunchConfiguration('namespace')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    urdf_model = LaunchConfiguration('urdf_model')
    use_namespace = LaunchConfiguration('use_namespace')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_rviz = LaunchConfiguration('use_rviz')
    use_simulator = LaunchConfiguration('use_simulator')
    world = LaunchConfiguration('world')

    # Declare the launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='True',
        description='Use simulation (Gazebo) clock if true')

    declare_use_joint_state_publisher_cmd = DeclareLaunchArgument(
        name='gui',
        default_value='False',
        description='Flag to enable joint_state_publisher_gui')
    
    declare_namespace_cmd = DeclareLaunchArgument(
        name='namespace',
        default_value='',
        description='Top-level namespace')
    
    declare_use_namespace_cmd = DeclareLaunchArgument(
        name='use_namespace',
        default_value='True',
        description='Whether to apply a namespace to the navigation stack')

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        name='rviz_config_file',
        default_value=default_rviz_config_path,
        description='Full path to the RVIZ config file to use')

    declare_simulator_cmd = DeclareLaunchArgument(
        name='headless',
        default_value='False',
        description='Whether to execute gzclient')

    declare_urdf_model_path_cmd = DeclareLaunchArgument(
        name='urdf_model',
        default_value=default_urdf_model_path,
        description='Absolute path to robot urdf file')

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name='use_rviz',
        default_value='False',
        description='Whether to start RVIZ')

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name='use_simulator',
        default_value='True',
        description='Whether to start the simulator')

    declare_world_cmd = DeclareLaunchArgument(
        name='world',
        default_value=world_path,
        description='Full path to the world model file to load')

    # Start Gazebo server
    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')),
        condition=IfCondition(use_simulator),
        launch_arguments={'world': world}.items())

    # Start Gazebo client
    start_gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')),
        condition=IfCondition(
            PythonExpression([use_simulator, ' and not ', headless])))

    twist_watchdog = Node(
        package='limo_gazebosim',
        executable='twist_watchdog.py',
        name='twist_watchdog'
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_joint_state_publisher_cmd)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_namespace_cmd)
    ld.add_action(declare_rviz_config_file_cmd)
    ld.add_action(declare_simulator_cmd)
    ld.add_action(declare_urdf_model_path_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(twist_watchdog)

    # Add actions to launch Gazebo
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_gazebo_client_cmd)

    # Define the robots with their unique names and positions
    robots = [
        {'name': 'limo1', 'x': '0.0', 'y': '0.0', 'yaw': '0.0'},
        # {'name': 'limo2', 'x': '1.0', 'y': '0.0', 'yaw': '0.0'}
    ]

    # Loop through each robot and launch the required nodes
    for robot in robots:
        ns = robot['name']

        # Start robot state publisher
        start_robot_state_publisher_cmd = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=ns,
            parameters=[{'robot_description': Command(['xacro ', urdf_model]),
                         'use_sim_time': use_sim_time}],
        )

        # Start joint state publisher
        start_joint_state_publisher_cmd = Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            namespace=ns,
            name='joint_state_publisher',
            condition=UnlessCondition(gui),
            parameters=[{'use_sim_time': use_sim_time}],
        )

        # Spawn the robot in Gazebo
        spawn_entity_cmd = Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', robot['name'],
                       '-x', robot['x'],
                       '-y', robot['y'],
                       '-z', spawn_z_val,
                       '-Y', robot['yaw'],
                       '-topic', 'robot_description',
                       '-robot_namespace', ns],
            output='screen'
        )

        # Add actions to the launch description
        ld.add_action(start_robot_state_publisher_cmd)
        ld.add_action(start_joint_state_publisher_cmd)
        ld.add_action(spawn_entity_cmd)

    # Launch RViz
    start_rviz_cmd = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file])

    ld.add_action(start_rviz_cmd)

    return ld
