# Rhino 8 + Python + VS Code Minimal Project

这是一个尽可能简单的 Rhino 8 建模项目：

- VS Code 负责编辑 `tools.py` 和各个 `build_*.py`
- Rhino 8 负责执行 `launcher.py`
- 每次运行都会 `reload` 最新模块并重建模型
- 自动生成的对象统一放到 `GeneratedGeometry` 图层

## 文件说明

- `tools.py`
  - 通用 Rhino 建模函数：基础几何、布尔运算、阵列、镜像、移动、旋转、多边形、由多边形生成面、由面生成实体
- `build_demo.py`
  - 一个独立模型；在这里写参数和 `build_model()`
  - 可复制为其他模型文件，例如 `build_house.py`
- `launcher.py`
  - 在 Rhino 中运行
  - 把项目目录加入 `sys.path`
  - `reload` `tools` 和当前选择的构建文件
  - 执行当前构建文件的 `build_model()`
- `README.md`
  - 使用说明

## 当前 demo

当前 `build_model()` 会创建并更新这些对象：

- Point
- Line
- Rectangle
- Circle
- Box
- Sphere
- Cylinder

其中 `Box`、`Sphere`、`Cylinder` 会左右排开，避免重叠，便于确认更新是否生效。

## tools.py 常用函数

所有函数接收 Rhino 对象 ID，并返回新对象 ID 或新对象 ID 列表。`boolean_union()` 和 `boolean_difference()` 默认删除参与运算的原实体；传入 `delete_input=False` 可以保留它们。

```python
# 布尔运算：参数是 Brep 对象 ID 的列表
joined_ids = tools.boolean_union([box_id, sphere_id])
cut_ids = tools.boolean_difference([box_id], [cylinder_id])

# 阵列：计数包含原对象
tools.rectangular_array(box_id, 4, 3, 25.0, 15.0)
tools.circular_array(box_id, center=(0.0, 0.0, 0.0), count=8)

# 变换：镜像默认复制；其他变换默认移动原对象
tools.mirror(box_id, plane_normal=(1.0, 0.0, 0.0))
tools.move(box_id, (10.0, 0.0, 0.0))
tools.rotate_2d(box_id, 45.0)
tools.rotate_3d(box_id, 30.0, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))

# 多边形 -> 面 -> 实体
polygon_id = tools.create_polygon(center=(0.0, 0.0), radius=10.0, sides=6)
face_id = tools.polygon_to_face(polygon_id)
solid_id = tools.face_to_solid(face_id, height=5.0)
```

## 首次在 Rhino 8 中运行

最简单的方法：

1. 打开 Rhino 8
2. 运行命令：`RunPythonScript`
3. 选择这个文件：

`/Users/bubble/Desktop/Model/Rhino/rhino_model/launcher.py`

运行后，Rhino 会执行 `launcher.py`，然后调用当前构建文件的 `build_model()`。

## Rhino 如何找到 VS Code 项目路径

当前做法最简单直接：

- 在 `launcher.py` 里写死项目路径：

```python
PROJECT_DIR = r"/Users/bubble/Desktop/Model/Rhino/rhino_model"
```

所以只要这个项目目录不变，Rhino 每次运行 `launcher.py` 时都能找到你的代码。

如果以后你移动了项目目录，只需要同步修改 `launcher.py` 里的 `PROJECT_DIR`。

## 日常工作流

```text
VS Code 修改 tools.py / build_demo.py
        ↓
保存
        ↓
回到 Rhino
        ↓
运行 launcher.py
        ↓
Rhino 删除旧的 GeneratedGeometry 对象并生成新的模型
```

## 从 VS Code 运行 Rhino

在 macOS 上，可以直接运行 `run_rhino.py`。它会激活 Rhino、运行 `_RunPythonScript`，再自动在文件选择框中定位并打开 `launcher.py`。Rhino 仍是实际执行建模代码的程序。

首次运行时，macOS 可能要求授权 VS Code（或你用来运行此文件的终端）控制电脑。在 `System Settings > Privacy & Security > Accessibility` 中允许它，然后再运行。运行时会暂时覆盖系统剪贴板内容。

如果输出提示找不到 Rhino，把 `run_rhino.py` 中的 `RHINO_APP_NAME` 改为 macOS 应用列表里显示的名称，例如 `Rhinoceros` 或 `Rhino 8`。

## 关于更新机制

每次运行 `build_model()` 时会执行：

1. 确保存在 `GeneratedGeometry` 图层
2. 删除该图层上的旧对象
3. 保留用户手动创建的其他图层和对象
4. 创建新的几何
5. 自动刷新视口

这意味着：

- 脚本只清理自己生成的对象
- 不会删除你手动建的其他模型

## 如何设置 Rhino Alias

可以，最简单的方式是把 Alias 指向 `RunPythonScript` 并附带脚本路径。

大致步骤：

1. Rhino 中打开 `Options`
2. 找到 `Aliases`
3. 新建一个别名，例如：`rr`
4. 命令内容填：

```text
! _RunPythonScript "/Users/bubble/Desktop/Model/Rhino/rhino_model/launcher.py"
```

之后你的工作流就会变成：

- 在 VS Code 保存
- 回到 Rhino
- 输入 `rr`

## 是否可以设置快捷键

可以。最简单的方法通常是：

1. 先创建上面的 Alias，例如 `rr`
2. 再在 Rhino 的键盘快捷键设置里，把某个快捷键绑定到这个 Alias 或对应命令

不同 Rhino 8 界面位置可能略有差异，但核心思路就是：

- 快捷键触发一个 Rhino 命令
- 这个 Rhino 命令再执行 `RunPythonScript` + `launcher.py`

如果你只想先快速开始，推荐先用 Alias，不必一开始就配快捷键。

## 切换不同模型

每一个构建文件都只需要提供一个同名入口：

```python
def build_model():
    ...
```

例如复制 `build_demo.py` 为 `build_house.py`，在其中创建房屋。然后在 `launcher.py` 中改一行：

```python
BUILD_MODULE = "build_house"
```

保存后运行 launcher，Rhino 会重载 `tools.py` 和 `build_house.py`，并生成该模型。

## 如何验证 reload 确实生效

最简单的验证方法：

1. 打开 `build_demo.py`
2. 把：

```python
box_l = 20.0
```

改成：

```python
box_l = 40.0
```

3. 保存
4. 回到 Rhino
5. 再运行 `launcher.py` 或输入你的 Alias

如果 Rhino 里的 box 明显变长，就说明 `build_demo.py` 已被重新加载。

你也可以改 `sphere_radius`、`cylinder_height` 或对象的位置。

只要重新运行 `launcher.py` 后模型变化了，就说明当前工作流已经成立。
