# UR5e MuJoCo Simulation

This package contains the UR5e model pipeline used to bring the official Universal Robots ROS 2 description into MuJoCo.

The main design decision is:

> **URDF/Xacro is the editable source of truth.**
>
> The MuJoCo MJCF model is generated from that source instead of maintaining a second hand-written UR5e model.

This keeps the robot description compatible with the normal ROS 2 / MoveIt workflow while still allowing MuJoCo-specific simulation configuration.

---

## 1. Current architecture

```text
Official Universal Robots `ur_description`
                  │
                  ▼
        urdf/ur5e.urdf.xacro
                  │
                xacro
                  ▼
        generated/ur5e.urdf
                  │
                  │  + mujoco/inputs.xml
                  ▼
mujoco_ros2_control URDF -> MJCF converter
                  │
                  ▼
 generated/mjcf/mujoco_description_formatted.xml
                  │
                  ▼
                MuJoCo
```

Two files define the model:

```text
urdf/ur5e.urdf.xacro
```

ROS-side robot description. This is where future robot additions belong, for example:

- tools
- TCP frames
- cameras
- fixed links
- visual geometry
- collision geometry

```text
mujoco/inputs.xml
```

MuJoCo-only information that URDF does not naturally describe, for example:

- MuJoCo defaults
- visual/collision classes
- actuator definitions
- actuator gains and limits
- integrator/options
- keyframes
- future MuJoCo-only sensors or simulation settings

The generated MJCF should not be manually edited. Changes should be made in the Xacro or `inputs.xml`, followed by regeneration.

---

## 2. Important package layout

Current relevant structure:

```text
ur5e_mujoco_sim/
├── CMakeLists.txt
├── package.xml
├── urdf/
│   └── ur5e.urdf.xacro
├── mujoco/
│   └── inputs.xml
└── generated/
    ├── ur5e.urdf
    └── mjcf/
        ├── assets/
        ├── mujoco_description.xml
        ├── mujoco_description_formatted.xml
        └── robot_description_formatted.urdf
```

`mujoco_description.xml` is an intermediate conversion result.

`mujoco_description_formatted.xml` is the final post-processed MJCF containing the converted visual/collision geometry plus the MuJoCo-specific inputs such as actuators and keyframes.

For this project, the generated model is currently kept inside the package so the exact tested MuJoCo model and converted assets can be tracked together with the source. The Xacro and `inputs.xml` remain the canonical editable sources.

---

## 3. UR5e Xacro source

The Xacro includes the official Universal Robots description:

```xml
<xacro:include
  filename="$(find ur_description)/urdf/ur_macro.xacro"/>
```

The UR5e is instantiated from the official macro and official configuration files:

```xml
<xacro:ur_robot
  name="ur5e"
  tf_prefix=""
  parent="world"
  joint_limits_parameters_file="$(find ur_description)/config/ur5e/joint_limits.yaml"
  kinematics_parameters_file="$(find ur_description)/config/ur5e/default_kinematics.yaml"
  physical_parameters_file="$(find ur_description)/config/ur5e/physical_parameters.yaml"
  visual_parameters_file="$(find ur_description)/config/ur5e/visual_parameters.yaml"
  safety_limits="false"
  safety_pos_margin="0.15"
  safety_k_position="20"
  force_abs_paths="true">

  <origin xyz="0 0 0" rpy="0 0 0"/>

</xacro:ur_robot>
```

`force_abs_paths="true"` is important for the conversion workflow because the converter needs to access the UR mesh files outside the normal ROS visualization pipeline.

During the successful test described here, `ur_description` resolved to the ROS Jazzy installation under:

```text
/opt/ros/jazzy/share/ur_description
```

If a pinned workspace copy of `ur_description` is built and sourced as an overlay, the resolved package location can instead come from that workspace.

---

## 4. MuJoCo-specific inputs

`mujoco/inputs.xml` supplements the URDF conversion.

The current model uses MuJoCo position actuators for all six UR5e joints:

```text
shoulder_pan_joint
shoulder_lift_joint
elbow_joint
wrist_1_joint
wrist_2_joint
wrist_3_joint
```

Current actuator configuration:

| Joint group | `kp` | `kv` | Force limit |
|---|---:|---:|---:|
| Shoulder pan / lift | 2000 | 400 | ±150 N·m |
| Elbow | 2000 | 400 | ±150 N·m |
| Wrist 1 / 2 / 3 | 500 | 100 | ±28 N·m |

The current home keyframe is:

```text
[-1.5708, -1.5708, 1.5708, -1.5708, -1.5708, 0]
```

The inputs file also defines the `visual` and `collision` MuJoCo classes required by the formatted converter output.

The current integrator is:

```xml
<option integrator="implicitfast"/>
```

---

## 5. One-time converter Python dependency

The `mujoco_ros2_control` conversion wrapper uses its own Python virtual environment:

```text
~/.ros/ros2_control/.venv
```

On the first UR5e conversion, DAE processing failed with:

```text
ImportError: missing `pip install pycollada`
```

Install the missing dependency into the converter's virtual environment:

```bash
~/.ros/ros2_control/.venv/bin/pip install pycollada
```

Verify it:

```bash
~/.ros/ros2_control/.venv/bin/python -c \
  "import collada; print(collada.__version__)"
```

The tested environment reported:

```text
0.9.3
```

Do not install this into an unrelated project virtual environment; the converter wrapper sources `~/.ros/ros2_control/.venv`.

---

## 6. Generate the URDF

From the workspace root:

```bash
cd ~/MuJoCoROSTrippleS
```

Generate the expanded URDF:

```bash
xacro \
  src/ur5e_mujoco_sim/urdf/ur5e.urdf.xacro \
  > src/ur5e_mujoco_sim/generated/ur5e.urdf
```

A useful check is:

```bash
grep -n "<mesh" \
  src/ur5e_mujoco_sim/generated/ur5e.urdf \
  | head -20
```

The generated mesh references should resolve to the installed/overlaid `ur_description` package.

---

## 7. Convert URDF to MJCF

Remove only the previous generated MJCF directory:

```bash
rm -rf src/ur5e_mujoco_sim/generated/mjcf
```

Run the `mujoco_ros2_control` wrapper:

```bash
ros2 run mujoco_ros2_control robot_description_to_mjcf.sh \
  --urdf src/ur5e_mujoco_sim/generated/ur5e.urdf \
  --mujoco_inputs src/ur5e_mujoco_sim/mujoco/inputs.xml \
  --output src/ur5e_mujoco_sim/generated/mjcf \
  --save_only
```

The converter generates OBJ assets and several XML/URDF files under:

```text
src/ur5e_mujoco_sim/generated/mjcf/
```

The important final model is:

```text
src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml
```

---

## 8. Validate the generated MJCF

Compile the final formatted MJCF with MuJoCo:

```bash
ros2 run mujoco_vendor compile \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_compiled.xml
```

A successful validation prints:

```text
Done.
```

The compiled XML is another derived validation artifact. The source remains the Xacro plus `mujoco/inputs.xml`.

---

## 9. Run the UR5e in MuJoCo

Launch the final formatted model:

```bash
ros2 run mujoco_vendor simulate \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml
```

At the current milestone, the UR5e:

- loads successfully in MuJoCo 3.4.0,
- has its converted visual meshes,
- has collision geometry,
- has all six revolute joints,
- has inertial properties from the official UR description,
- has six MuJoCo position actuators,
- remains stable instead of behaving as an uncontrolled passive mechanism.

This establishes the basic robot-model pipeline before adding ROS 2 control and trajectory controllers.

---

## 10. Checks for the generated model

Check that the six actuators exist:

```bash
grep -n -A35 '<actuator>' \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml
```

Check the home keyframe:

```bash
grep -n -A5 '<keyframe>' \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml
```

Check the converted joints:

```bash
grep -n '<joint' \
  src/ur5e_mujoco_sim/generated/mjcf/mujoco_description_formatted.xml
```

---

## 11. Problems encountered during setup

### Native MuJoCo URDF compilation could not resolve UR mesh paths

Trying to compile the expanded URDF directly:

```bash
ros2 run mujoco_vendor compile \
  generated/ur5e.urdf \
  generated/ur5e.xml
```

failed with an error similar to:

```text
Error opening file '.../base.stl': No such file or directory
```

Even though the Xacro could generate `file:///...` mesh paths, the native URDF import path was not sufficient for this ROS model.

**Solution:** use the dedicated `mujoco_ros2_control` URDF-to-MJCF converter.

---

### Running the converter without `--urdf`

Running:

```bash
ros2 run mujoco_ros2_control robot_description_to_mjcf.sh
```

without a URDF argument caused it to wait for a ROS `robot_description` parameter service.

For the current offline generation workflow, always pass:

```text
--urdf <generated URDF>
```

---

### Missing `pycollada`

The converter processes the official UR `.dae` visual meshes with Python/trimesh.

The initial conversion stopped with:

```text
ImportError: missing `pip install pycollada`
```

**Solution:**

```bash
~/.ros/ros2_control/.venv/bin/pip install pycollada
```

---

### Embedding `<mujoco_inputs>` directly in the URDF did not work

Putting:

```xml
<mujoco_inputs>
  ...
</mujoco_inputs>
```

directly inside the generated robot description produced warnings such as:

```text
Unknown tag "mujoco_inputs" in /robot[@name='ur5e']
```

and no actuators appeared in the generated intermediate MJCF.

**Solution:** keep MuJoCo-specific configuration in:

```text
mujoco/inputs.xml
```

and pass it explicitly using:

```text
--mujoco_inputs src/ur5e_mujoco_sim/mujoco/inputs.xml
```

---

### Intermediate versus final MJCF

The converter creates:

```text
mujoco_description.xml
```

and:

```text
mujoco_description_formatted.xml
```

The first file is an intermediate structural conversion and can lack the post-processed MuJoCo additions.

The final model to validate and simulate is:

```text
mujoco_description_formatted.xml
```

This final file contains the decomposed/material-aware meshes, visual and collision geoms, MuJoCo inputs, actuators, and keyframes.

---

### Missing MuJoCo `visual` / `collision` defaults

The formatted output references geoms with:

```xml
class="visual"
```

and:

```xml
class="collision"
```

The MuJoCo inputs therefore need matching default definitions.

After adding these defaults to `mujoco/inputs.xml`, the generated formatted model displayed and behaved correctly.

---

## 12. Current milestone

The robot-description side is now working:

```text
Official UR description
        ↓
custom Xacro wrapper
        ↓
expanded URDF
        ↓
MuJoCo-specific inputs
        ↓
mujoco_ros2_control converter
        ↓
formatted MJCF + assets
        ↓
MuJoCo 3.4.0
```

The next stage is intentionally separate:

```text
ROS 2 control
    ↓
mujoco_ros2_control hardware interface
    ↓
controller_manager
    ↓
joint_state_broadcaster
    ↓
joint_trajectory_controller
    ↓
UR5e joint motion from ROS 2
```

Do not mix this next control stage into the model-generation work until the current model milestone has been committed and preserved.