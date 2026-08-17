# MuJoCoROSTrippleS

ROS 2 and MuJoCo robotics simulation workspace.

## Goals

- Run maintained robot models in MuJoCo.
- Control simulated robots through standard ROS 2 interfaces.
- Keep simulation and real-robot interfaces compatible where practical.
- Develop reusable C++ robotics software.
- Extend the system later toward navigation and reinforcement learning.

## Workspace

```bash
git clone https://github.com/Sohaib-Snouber/MuJoCoROSTrippleS.git
cd MuJoCoROSTrippleS

rosdep update

vcs import src/third_party < dependencies.repos

rosdep install \
  --from-paths src \
  --ignore-src \
  -r \
  -y

colcon build

source install/setup.bash
```

