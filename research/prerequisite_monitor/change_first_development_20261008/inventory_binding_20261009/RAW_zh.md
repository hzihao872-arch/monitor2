## q07108c1875aa88b5

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "orange square plate on gray box", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o2", "description": "gray box with transparent side", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "gray cube on orange plate", "part_of": "o1", "visible_state": "visibly connected component"}, {"id": "o4", "description": "white robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{
  "context": "A blue cube rests on a wooden surface near a gray box with a transparent side, which holds an orange plate with a gray cube on it. A white robotic arm is positioned nearby.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0005",
      "object": "o3",
      "before": "gray cube on orange plate, robot arm approaching",
      "after": "gray cube lifted by robot arm, orange plate now partially empty"
    },
    {
      "b": "f0006",
      "a": "f0007",
      "object": "o2",
      "before": "gray box with orange plate and gray cube on top",
      "after": "gray box with orange plate and empty space where gray cube was"
    },
    {
      "b": "f0009",
      "a": "f0011",
      "object": "o3",
      "before": "gray cube held by robot arm above box",
      "after": "gray cube placed back on orange plate, robot arm retracted"
    }
  ],
  "coverage": "complete"
}

```

## q07e7773ad34d85f6

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "pink cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o2", "description": "gray rectangular bar with yellow and green top", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "gray robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}, {"id": "o4", "description": "gray cylindrical base of robotic arm", "part_of": "o3", "visible_state": "visibly connected to robotic arm"}], "coverage": "complete"}

```

TRACK

```json

{"context":"A robotic arm on a wooden surface interacts with a yellow platform holding a gray cube and a pink cube, while a blue cube remains separate.","changes":[{"b":"f0004","a":"f0010","object":"o1","before":"pink cube on yellow platform","after":"pink cube moved off platform and onto wooden surface"},{"b":"f0006","a":"f0010","object":"o2","before":"gray bar with yellow and green top on platform","after":"gray bar partially detached from platform and lying on surface"},{"b":"f0008","a":"f0010","object":"o0","before":"blue cube on wooden surface","after":"blue cube remains on wooden surface, no change"}],"coverage":"complete"}

```

## q0d6f6ef3062d4d34

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "orange square with small gray cube on top", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o2", "description": "gray box with transparent sides and orange top", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "white robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}, {"id": "o4", "description": "white cylindrical object partially visible", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{"context":"A blue cube, an orange square with a gray cube on top, and a gray box with transparent sides sit on a wooden surface as a white robotic arm moves toward them.","changes":[{"b":"f0003","a":"f0004","object":"o1","before":"gray cube on orange square","after":"gray cube lifted by robotic arm"},{"b":"f0004","a":"f0005","object":"o1","before":"gray cube lifted by robotic arm","after":"gray cube held by robotic arm above orange square"},{"b":"f0005","a":"f0006","object":"o1","before":"gray cube held by robotic arm above orange square","after":"gray cube placed on orange square"}],"coverage":"complete"}

```

## q613a0d8ddf5acc68

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "orange square platform on gray box", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o2", "description": "gray box with transparent side", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "gray cube on orange platform", "part_of": "o1", "visible_state": "visibly connected component"}, {"id": "o4", "description": "white robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{
  "context": "A blue cube rests on a wooden surface near a robotic arm. A gray box with a transparent side holds an orange platform with a gray cube on top.",
  "changes": [
    {
      "b": "f0003",
      "a": "f0004",
      "object": "o3",
      "before": "gray cube on orange platform",
      "after": "gray cube lifted by robotic arm"
    },
    {
      "b": "f0004",
      "a": "f0006",
      "object": "o2",
      "before": "gray box with transparent side and orange platform",
      "after": "gray box with transparent side and orange platform partially removed"
    },
    {
      "b": "f0006",
      "a": "f0010",
      "object": "o3",
      "before": "gray cube held by robotic arm",
      "after": "gray cube placed back on orange platform"
    }
  ],
  "coverage": "complete"
}

```

## q675f22bca6b91b54

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "pink cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o2", "description": "gray rectangular bar with yellow and green top", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "gray cube on yellow surface", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o4", "description": "white robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{
  "context": "A robotic arm moves toward a blue cube on a wooden surface, then picks it up and places it on a yellow platform with other cubes.",
  "changes": [
    {
      "b": "f0000",
      "a": "f0005",
      "object": "o0",
      "before": "blue cube on wooden surface",
      "after": "blue cube held by robotic arm"
    },
    {
      "b": "f0005",
      "a": "f0011",
      "object": "o0",
      "before": "blue cube held by robotic arm",
      "after": "blue cube placed on yellow platform"
    },
    {
      "b": "f0000",
      "a": "f0014",
      "object": "o2",
      "before": "gray rectangular bar with yellow and green top",
      "after": "gray rectangular bar with yellow and green top, now with blue cube on top"
    }
  ],
  "coverage": "complete"
}

```

## qbb0dbd57d63ce6a9

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "pink cube with green stick attached", "part_of": "o1", "visible_state": "visibly connected component"}, {"id": "o2", "description": "gray cube on yellow platform", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o3", "description": "green stick lying on gray rail", "part_of": "o3", "visible_state": "visibly connected component"}, {"id": "o4", "description": "gray rail with yellow platform and green stick", "part_of": null, "visible_state": "assembled structure"}], "coverage": "complete"}

```

## qcde827bb66b99fd4

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "pink cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o2", "description": "gray cube on yellow platform", "part_of": "o3", "visible_state": "visibly connected component"}, {"id": "o3", "description": "yellow platform with gray cube on it", "part_of": "o4", "visible_state": "visibly connected component"}, {"id": "o4", "description": "gray track with yellow platform and green rods", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{"context":"A robot manipulates a gray cube on a yellow platform, which is part of a gray track with green rods, while a blue and pink cube remain stationary on a wooden surface.","changes":[{"b":"f0005","a":"f0006","object":"o2","before":"gray cube on yellow platform","after":"gray cube lifted off yellow platform"},{"b":"f0006","a":"f0007","object":"o2","before":"gray cube held by robot above yellow platform","after":"gray cube placed on yellow platform"},{"b":"f0008","a":"f0009","object":"o1","before":"pink cube stationary on wooden surface","after":"pink cube moved onto yellow platform"}],"coverage":"complete"}

```

## qf2bed1caaecc37a0

INVENTORY

```json

{"objects": [{"id": "o0", "description": "blue cube on wooden surface", "part_of": null, "visible_state": "standalone item"}, {"id": "o1", "description": "orange square with small gray cube on top", "part_of": "o2", "visible_state": "visibly connected component"}, {"id": "o2", "description": "gray box with transparent sides and orange top", "part_of": null, "visible_state": "standalone item"}, {"id": "o3", "description": "white robotic arm with black joints", "part_of": null, "visible_state": "standalone item"}, {"id": "o4", "description": "gray cylindrical object partially visible", "part_of": null, "visible_state": "standalone item"}], "coverage": "complete"}

```

TRACK

```json

{
  "context": "A robotic arm manipulates a blue cube on a wooden surface near a transparent box with an orange top and a small gray cube on it.",
  "changes": [
    {
      "b": "f0004",
      "a": "f0005",
      "object": "o0",
      "before": "blue cube on wooden surface",
      "after": "blue cube held by robotic arm"
    },
    {
      "b": "f0008",
      "a": "f0010",
      "object": "o0",
      "before": "blue cube held by robotic arm above box",
      "after": "blue cube inside transparent box"
    },
    {
      "b": "f0000",
      "a": "f0014",
      "object": "o1",
      "before": "gray cube on orange square",
      "after": "gray cube remains on orange square"
    }
  ],
  "coverage": "complete"
}

```