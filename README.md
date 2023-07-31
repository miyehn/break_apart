Last updated: 7/30/23

[Latest version download](addons/break_apart.py), [link to repository](https://github.com/miyehn/break_apart)

![panel](media/panel.png)

## Merge threshold

It's the threshold used for when you press shift + S to merge vertices by distance.

## Break Apart

Set the object to break apart as "Target",

Select the cookie cutter object,

Hit the "break apart" button.

[Example video](media/break.mp4)

Btw [here](media/boulder_cutter.fbx) is a boulder mesh I've been using to cut things.

## Export FBX

Set the output folder (relative to the current .blend file) and fbx filename (without extension). 

Select the mesh(es) you wish to export.
 - Note that the last selected mesh (aka active object) will be used to determine the anchor position of your exported fbx.

Hit "Export FBX".
 - If you had only one mesh selected, it will be renamed to the filename
 - If you had multiple meshes, a plain axes node called your filename will be created, with all your meshes as its children.

## Hotkeys

These are actions I use a lot when modeling. Let me know if you'd like to add something else.

 - shift + B: break apart
 - shift + L: select linked
 - shift + M: select non-manifold (need to be in vertex or edge editing mode)
 - shift + N: toggle face orientation overlay
 - shift + T: triangulate selected faces
 - shift + V: merge (vertices) at last
 - shift + S: merge by distance with specified threshold

## Contact

Find me on discord (`miyehn`) if you need help or would like to provide feedback.
