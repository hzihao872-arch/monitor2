# 原compact2与15全帧目标盲发现：原答对照
所有案例为开发素材；以下输出不进行修复，也不自动追认为语义正确。

## q07108c1875aa88b5

原8帧+4自动裁剪：
```json
{
  "context": "A robot manipulates a box on a wooden surface with a blue cube nearby.",
  "changes": [
    {
      "b": "f0005",
      "a": "f0008",
      "object": "robot arm and box",
      "before": "robot arm above box, orange top with brown cube visible",
      "after": "robot arm has removed brown cube, box top is open and empty"
    },
    {
      "b": "f0008",
      "a": "f0010",
      "object": "robot arm and box",
      "before": "robot arm above open box, orange top visible",
      "after": "robot arm has placed brown cube back on orange top"
    },
    {
      "b": "f0010",
      "a": "f0011",
      "object": "robot arm and box",
      "before": "robot arm above box with brown cube on orange top",
      "after": "robot arm has retracted, box top is closed"
    }
  ],
  "coverage": "complete"
}
```

15合法全帧：
```json
{
  "context": "A robot arm moves toward a box with an orange top and a small brown block on it, while a blue cube rests on the wooden floor nearby.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0004",
      "object": "robot arm",
      "before": "retracted, positioned above the box",
      "after": "extended downward, grasping the brown block"
    },
    {
      "b": "f0006",
      "a": "f0007",
      "object": "box top",
      "before": "intact with orange surface and brown block on it",
      "after": "partially lifted, revealing the box's dark interior"
    },
    {
      "b": "f0011",
      "a": "f0012",
      "object": "robot arm",
      "before": "retracted, positioned above the box",
      "after": "extended downward, grasping the brown block"
    }
  ],
  "coverage": "complete"
}
```

## q07e7773ad34d85f6

原8帧+4自动裁剪：
```json
{
  "context": "A robotic arm is positioned over a wooden surface with scattered blocks and a yellow platform.",
  "changes": [
    {
      "b": "f0002",
      "a": "f0005",
      "object": "robotic arm",
      "before": "arm extended, gripper open, positioned above pink and yellow objects",
      "after": "arm lowered, gripper closed, grasping the pink object"
    },
    {
      "b": "f0007",
      "a": "f0008",
      "object": "robotic arm",
      "before": "arm holding pink object, gripper closed, positioned over yellow platform",
      "after": "arm holding pink object, gripper closed, slightly repositioned over yellow platform"
    },
    {
      "b": "f0010",
      "a": "f0011",
      "object": "pink object",
      "before": "held by robotic arm, positioned above yellow platform",
      "after": "released onto wooden surface, now separate from arm"
    }
  ],
  "coverage": "complete"
}
```

15合法全帧：
```json
{
  "context": "A robotic arm is positioned over a wooden surface with scattered blocks and a yellow platform.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0005",
      "object": "robotic arm",
      "before": "arm extended toward pink block and yellow platform",
      "after": "arm grasping the gray block on the yellow platform"
    },
    {
      "b": "f0009",
      "a": "f0011",
      "object": "pink block",
      "before": "resting on the yellow platform",
      "after": "moved off the platform and lying on the wooden surface"
    },
    {
      "b": "f0010",
      "a": "f0012",
      "object": "robotic arm",
      "before": "releasing the gray block onto the yellow platform",
      "after": "retracted and positioned above the pink block"
    }
  ],
  "coverage": "complete"
}
```

## q0d6f6ef3062d4d34

原8帧+4自动裁剪：
```json
{"context":"A robotic arm and a blue cube are on a wooden surface near a transparent box with an orange top.","changes":[{"b":"f0003","a":"f0005","object":"robot arm","before":"retracted","after":"extended toward box"},{"b":"f0008","a":"f0011","object":"robot arm","before":"holding orange top","after":"releasing orange top"},{"b":"f0011","a":"f0014","object":"robot arm","before":"retracted","after":"extended toward box"}],"coverage":"complete"}
```

15合法全帧：
```json
{"context":"A robot arm moves toward a box with an orange top, then retracts after interacting with an object on it.","changes":[{"b":"f0003","a":"f0008","object":"robot arm","before":"reaching toward orange top","after":"grasping object on orange top"},{"b":"f0008","a":"f0010","object":"robot arm","before":"holding object on orange top","after":"retracting from orange top"},{"b":"f0000","a":"f0014","object":"orange top","before":"object resting on it","after":"object resting on it"}],"coverage":"complete"}
```

## q613a0d8ddf5acc68

原8帧+4自动裁剪：
```json
{
  "context": "A robot arm interacts with a box on a wooden surface, with a blue cube nearby.",
  "changes": [
    {
      "b": "c0a",
      "a": "c1a",
      "object": "robot arm",
      "before": "arm partially visible, positioned above the box",
      "after": "arm fully visible, gripping an object on the box"
    },
    {
      "b": "f0005",
      "a": "f0008",
      "object": "box",
      "before": "box has a solid top surface with an object on it",
      "after": "box top surface is removed, revealing an empty interior"
    },
    {
      "b": "f0011",
      "a": "f0014",
      "object": "robot arm",
      "before": "arm holding an object over the box",
      "after": "arm has released the object, now stationary"
    }
  ],
  "coverage": "complete"
}
```

15合法全帧：
```json
{"context":"A robot arm moves toward a box with an orange top and a small brown block on it, while a blue cube rests on the wooden floor nearby.","changes":[{"b":"f0003","a":"f0004","object":"robot arm","before":"retracted, above the box","after":"extended, grasping the brown block"},{"b":"f0006","a":"f0007","object":"box top","before":"intact with brown block on it","after":"partially removed, revealing the box interior"},{"b":"f0007","a":"f0008","object":"robot arm","before":"holding the brown block","after":"releasing the block onto the box top"}],"coverage":"complete"}
```

## q675f22bca6b91b54

原8帧+4自动裁剪：
```json
{"context":"A robot arm manipulates blocks on a wooden surface near a yellow platform with other blocks.","changes":[{"b":"f0005","a":"f0007","object":"blue cube","before":"held by robot arm","after":"placed on yellow platform"},{"b":"f0006","a":"f0008","object":"blue cube","before":"held by robot arm","after":"placed on yellow platform"},{"b":"f0011","a":"f0014","object":"blue cube","before":"on yellow platform","after":"on yellow platform"}],"coverage":"complete"}
```

15合法全帧：
```json
{
  "context": "A robotic arm and colored blocks on a wooden surface with a grid floor in the background.",
  "changes": [
    {
      "b": "f0000",
      "a": "f0007",
      "object": "blue cube",
      "before": "on the wooden surface, away from the robotic arm",
      "after": "held by the robotic arm"
    },
    {
      "b": "f0007",
      "a": "f0011",
      "object": "blue cube",
      "before": "held by the robotic arm",
      "after": "placed on the yellow platform"
    },
    {
      "b": "f0000",
      "a": "f0014",
      "object": "robotic arm",
      "before": "stationary, positioned above the blue cube",
      "after": "stationary, positioned above the yellow platform"
    }
  ],
  "coverage": "complete"
}
```

## qbb0dbd57d63ce6a9

原8帧+4自动裁剪：
```json
{
  "context": "A robotic arm is positioned over a wooden surface with scattered blocks and a yellow platform.",
  "changes": [
    {
      "b": "c0a",
      "a": "c1a",
      "object": "robotic arm",
      "before": "arm extended over yellow platform with gray block on it",
      "after": "arm retracted, gray block still on yellow platform"
    },
    {
      "b": "c1b",
      "a": "c1a",
      "object": "pink block",
      "before": "visible on wooden surface near yellow platform",
      "after": "moved onto yellow platform by robotic arm"
    },
    {
      "b": "f0000",
      "a": "f0014",
      "object": "robotic arm",
      "before": "arm extended over yellow platform",
      "after": "arm retracted to initial position"
    }
  ],
  "coverage": "complete"
}
```

15合法全帧：
```json
{
  "context": "A robotic arm is positioned above a wooden surface with scattered blocks and a yellow platform.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0011",
      "object": "robotic arm",
      "before": "arm extended toward the yellow platform",
      "after": "arm retracted to initial position"
    },
    {
      "b": "f0005",
      "a": "f0009",
      "object": "gray cube",
      "before": "on yellow platform",
      "after": "on yellow platform"
    },
    {
      "b": "f0007",
      "a": "f0012",
      "object": "pink cube",
      "before": "on green bar",
      "after": "on green bar"
    }
  ],
  "coverage": "complete"
}
```

## qcde827bb66b99fd4

原8帧+4自动裁剪：
```json
{"context":"Robot arm and blocks on wooden surface with grid floor in background.","changes":[{"b":"f0000","a":"f0005","object":"robot arm","before":"retracted","after":"extended over yellow platform"},{"b":"f0005","a":"f0011","object":"pink block","before":"on platform","after":"moved to side of platform"},{"b":"f0008","a":"f0014","object":"green bar","before":"on platform","after":"on platform with pink block"}],"coverage":"complete"}
```

15合法全帧：
```json
{
  "context": "A robotic arm is positioned above a wooden surface with scattered colored blocks and a yellow platform.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0005",
      "object": "robotic arm",
      "before": "arm extended toward yellow platform",
      "after": "arm grasping gray block on yellow platform"
    },
    {
      "b": "f0005",
      "a": "f0007",
      "object": "gray block",
      "before": "on yellow platform",
      "after": "lifted by robotic arm"
    },
    {
      "b": "f0008",
      "a": "f0010",
      "object": "pink block",
      "before": "partially occluded by robotic arm",
      "after": "visible on wooden surface near yellow platform"
    }
  ],
  "coverage": "complete"
}
```

## qf2bed1caaecc37a0

原8帧+4自动裁剪：
```json
{"context":"A robot manipulates a blue cube on a wooden surface near a transparent box with an orange lid.","changes":[{"b":"f0005","a":"f0007","object":"blue cube","before":"held by robot","after":"placed into transparent box"},{"b":"f0006","a":"f0008","object":"blue cube","before":"held by robot","after":"placed into transparent box"},{"b":"f0011","a":"f0014","object":"blue cube","before":"inside transparent box","after":"inside transparent box"}],"coverage":"complete"}
```

15合法全帧：
```json
{"context":"A robotic arm and a blue cube on a wooden surface near a transparent box with an orange lid.","changes":[{"b":"f0000","a":"f0009","object":"blue cube","before":"on wooden surface","after":"inside transparent box"},{"b":"f0000","a":"f0012","object":"blue cube","before":"on wooden surface","after":"inside transparent box"},{"b":"f0000","a":"f0014","object":"robot arm","before":"stationary","after":"stationary"}],"coverage":"complete"}
```