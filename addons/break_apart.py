bl_info = {
	"name": "Break Apart",
	"author": "miyehn",
 	"version" : (0, 3, 0),
	"blender": (3, 6, 0),
	"doc_url": "https://miyehn.me/break_apart/",
	"category": "Shepherds",
}

import bpy
import os

#=========================== OPERATORS =============================

def prnt(ctx, obj):
	ctx.report({'INFO'}, obj.name)

class BA_OT_toggle_seam(bpy.types.Operator):
	bl_idname="ba.toggle_seam"
	bl_label="Toggle Seam"
	bl_options={'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.object.mode_set(mode='OBJECT')

		obj = bpy.context.active_object
		allSeam = True
		numSelected = 0
		for e in obj.data.edges:
			if e.select:
				numSelected += 1
				if not e.use_seam:
					allSeam = False

		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.mark_seam(clear=allSeam)

		return {'FINISHED'}

class BA_OT_toggle_sharp(bpy.types.Operator):
	bl_idname="ba.toggle_sharp"
	bl_label="Toggle Sharp"
	bl_options={'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.object.mode_set(mode='OBJECT')

		obj = bpy.context.active_object
		allSharp = True
		numSelected = 0
		for e in obj.data.edges:
			if e.select:
				numSelected += 1
				if not e.use_edge_sharp:
					allSharp = False

		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.mark_sharp(clear=allSharp)

		return {'FINISHED'}


class BA_OT_merge_by_ba_threshold(bpy.types.Operator):
	bl_idname="ba.merge_by_ba_threshold"
	bl_label="Merge by BAThreshold"
	bl_options={'REGISTER', 'UNDO'}

	def execute(self, context):
		threshold = bpy.context.scene.baProps.mergeThreshold
		bpy.ops.mesh.remove_doubles(threshold=threshold)
		return {'FINISHED'}

class BA_OT_toggle_face_orientation(bpy.types.Operator):
	bl_idname="ba.toggle_face_orientation"
	bl_label="Toggle Face Orientation"
	bl_options={'REGISTER', 'UNDO'}

	def execute(self, context):
		for area in context.screen.areas:
			if area.type == 'VIEW_3D':
				for space in area.spaces:
					if space.type == 'VIEW_3D':
						space.overlay.show_face_orientation = not space.overlay.show_face_orientation
		return {'FINISHED'}

class BA_OT_break_apart(bpy.types.Operator):
	bl_idname="ba.break_apart"
	bl_label="Break Apart!"
	bl_options={'REGISTER', 'UNDO'}

	@classmethod
	def description(cls, context, properties):
		return "Make a cut on the target mesh using the selected object"

	def execute(self, context):

		target = bpy.context.scene.baProps.target

		if not bpy.context.object.mode=='OBJECT':
			self.report({'WARNING'}, "This op is only available in object mode (4).")
			return {'FINISHED'}

		# check if target is set
		if target is None:
			self.report({'WARNING'}, "Please set the target object to break apart")
			return {'FINISHED'}

		# check if there's an object selected
		if not len(bpy.context.selected_objects)==1:
			self.report({'WARNING'}, "Please have exactly one object (the cookie cutter) selected")
			return {'FINISHED'}

		# boulder cannot be the selected obj
		boulder = bpy.context.selected_objects[0]
		if target == boulder:
			self.report({'WARNING'}, "The selected object must be different from the boulder")
			return {'FINISHED'}

		#==== proceed to operations ====

		# select target
		boulder.select_set(False)
		target.select_set(True)
		# store its material if it has one (not necessary?)
		target_material = None
		if len(target.data.materials) > 0:
			target_material = target.data.materials[0]

		# duplicate target to get cutout part
		bpy.ops.object.duplicate(linked=False)
		target_cut = bpy.context.selected_objects[0]
		target_cut.name = target.name + "_cutout"

		# add modifier for target_cut: https://docs.blender.org/api/current/bpy.types.BooleanModifier.html
		boolmod = target_cut.modifiers.new("baBool", 'BOOLEAN')
		boolmod.object = boulder
		boolmod.operation = 'INTERSECT'
		boolmod.solver = 'EXACT'
		# apply it
		bpy.context.view_layer.objects.active = target_cut
		bpy.ops.object.modifier_apply(modifier="baBool")

		# add modifier for target
		boolmod = target.modifiers.new("baBool", 'BOOLEAN')
		boolmod.object = boulder
		boolmod.operation = 'DIFFERENCE'
		boolmod.solver = 'EXACT'
		# apply it
		bpy.context.view_layer.objects.active = target
		bpy.ops.object.modifier_apply(modifier="baBool")

		# apply materials (not necessary?)
		if not target_material is None:
			pass
			#target.data.materials.clear()
			#target.data.materials.append(target_material)
			#target_cut.data.materials.clear()
			#target_cut.data.materials.append(target_material)

		# hide the cutout part
		target_cut.hide_set(True)

		return {'FINISHED'}


class BA_OT_open_export_folder(bpy.types.Operator):
	bl_idname="ba.open_export_folder"
	bl_label="Open Folder"
	bl_options={'REGISTER', 'UNDO'}

	def execute(self, context):
		folder = BA_OT_export_fbx.getExportFolder()
		if not os.path.exists(folder):
			self.report({'WARNING'}, "This folder doesn't exist yet.")
			return {'FINISHED'}

		os.startfile(folder)
		return {'FINISHED'}


class BA_OT_export_fbx(bpy.types.Operator):
	bl_idname="ba.export_fbx"
	bl_label="Export FBX"
	bl_options={'REGISTER', 'UNDO'}

	@staticmethod
	def getExportFolder():
		# see: https://docs.blender.org/api/current/bpy.ops.export_scene.html
		directory = bpy.context.scene.baProps.exportDirectory
		lastChar = ''
		if len(directory) > 0:
			lastChar = directory[len(directory)-1]
		else:
			directory='.'

		if lastChar == '/' or lastChar == '\\':
			directory = directory[:-1]

		fullDirectory = bpy.path.abspath("//" + directory)
		return fullDirectory

	@classmethod
	def description(cls, context, properties):
		return "Process and export selected objects to fbx"

	def execute(self, context):

		if not bpy.data.is_saved:
			self.report({'WARNING'}, "export failed: .blend file is not saved to disc yet")
			return {'FINISHED'}

		fullDirectory = BA_OT_export_fbx.getExportFolder()

		if not os.path.exists(fullDirectory):
			os.makedirs(fullDirectory)

		filename = bpy.context.scene.baProps.exportFilename
		fullPath = fullDirectory + '\\' + filename + '.fbx'

		# actually operate on the scene:

		objects = bpy.context.selected_objects

		if len(objects) == 0:
			self.report({'WARNING'}, "Please first select the objects you want to export")
			return {'FINISHED'}

		mainObj = bpy.context.active_object
		if len(objects) > 1:
			collection = mainObj.users_collection[0]
			bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=mainObj.matrix_world.translation, scale=(1,1,1))
			empty = bpy.context.active_object
			empty.users_collection[0].objects.unlink(empty)
			collection.objects.link(empty)

			for obj in objects:
				obj.select_set(state=True)
			empty.select_set(state=True)
			bpy.context.view_layer.objects.active = empty
			mainObj = empty

		bpy.ops.object.parent_set(type='OBJECT')

		mainObj.name = filename

		# now: actually export...
		bpy.ops.export_scene.fbx(
			filepath=fullPath,
			use_selection=True,
			object_types={'EMPTY', 'MESH'},
			use_triangles=True
			)

		self.report({'INFO'}, fullPath)

		return {'FINISHED'}


#=========================== PROPERTIES ============================

class BAProperties(bpy.types.PropertyGroup):

	target: bpy.props.PointerProperty(
		type=bpy.types.Object,
		name="Target",
		description="The object you want to cut"
		)

	mergeThreshold: bpy.props.FloatProperty(
		name="Merge Threshold",
		default=0.03,
		soft_min=0.00001,
		soft_max=0.1,
		step=0.01
		)

	exportDirectory: bpy.props.StringProperty(
		name="Folder",
		description="fbx export directory, relative to this .blend file",
		default="",
		maxlen=256
		)

	exportFilename: bpy.props.StringProperty(
		name="Filename",
		description="file name without extension",
		default="testMesh",
		maxlen=256
		)


#============================= PANEL ===============================

class BA_PT_tools_panel(bpy.types.Panel):
	bl_label = "Break Apart"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Break Apart"

	def draw(self, context):
		row = self.layout.row()
		row.label(text="Baaaa!", icon='GHOST_ENABLED')

		self.layout.row().separator()
		row = self.layout.row()
		row.prop(context.scene.baProps, "mergeThreshold")

		self.layout.row().separator()
		row = self.layout.row()
		row.prop(context.scene.baProps, "target")

		row = self.layout.row()
		row.operator("ba.break_apart")

		self.layout.row().separator()

		row = self.layout.row()
		row.label(text="Export selected:")

		row = self.layout.row();
		row.prop(context.scene.baProps, "exportDirectory")

		row = self.layout.row();
		row.prop(context.scene.baProps, "exportFilename")

		row = self.layout.row()
		row.operator("ba.export_fbx")
		row.operator("ba.open_export_folder")

#=========================== KEYMAPS ===============================

addon_keymaps = []

def init_keymaps():
	kc = bpy.context.window_manager.keyconfigs.addon
	km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

	# modeling & uv:

	kmi_selectLinked = km.keymap_items.new("mesh.select_linked", 'Q', 'PRESS', shift=True)

	# modeling

	kmi_breakApart = km.keymap_items.new("ba.break_apart", 'B', 'PRESS', shift=True)
	kmi_selectNonManifold = km.keymap_items.new("mesh.select_non_manifold", 'M', 'PRESS', shift=True)
	kmi_toggleFaceOrientation = km.keymap_items.new("ba.toggle_face_orientation", 'N', 'PRESS', shift=True)
	kmi_triangulate = km.keymap_items.new("mesh.quads_convert_to_tris", 'T', 'PRESS', shift=True)
	kmi_mergeLast = km.keymap_items.new("mesh.merge", 'V', 'PRESS', shift=True)
	kmi_mergeLast.properties.type='LAST'
	kmi_mergeByDist = km.keymap_items.new("ba.merge_by_ba_threshold", 'D', 'PRESS', shift=True)

	# uv
	kmi_unwrap = km.keymap_items.new("uv.unwrap", 'W', 'PRESS', shift=True)
	kmi_seam = km.keymap_items.new("ba.toggle_seam", 'S', 'PRESS', shift=True)
	kmi_sharp = km.keymap_items.new("ba.toggle_sharp", 'S', 'PRESS', shift=False)
	kmi_selectPrevActive = km.keymap_items.new("mesh.select_prev_item", 'LEFT_ARROW', 'PRESS', shift=False)
	kmi_selectNextActive = km.keymap_items.new("mesh.select_next_item", 'RIGHT_ARROW', 'PRESS', shift=False)

	kmi = [
		kmi_breakApart,
		kmi_selectLinked,
		kmi_selectNonManifold,
		kmi_toggleFaceOrientation,
		kmi_triangulate,
		kmi_mergeLast,
		kmi_mergeByDist,
		kmi_unwrap,
		kmi_selectPrevActive,
		kmi_selectNextActive
	]
	return km, kmi

#========================= REGISTRATION =============================

classes = (
	BAProperties,
	BA_OT_toggle_seam,
	BA_OT_toggle_sharp,
	BA_OT_toggle_face_orientation,
	BA_OT_merge_by_ba_threshold,
	BA_OT_break_apart,
	BA_OT_export_fbx,
	BA_OT_open_export_folder,
	BA_PT_tools_panel
)

def register():
	for cls in classes: bpy.utils.register_class(cls)

	# global props
	bpy.types.Scene.baProps = bpy.props.PointerProperty(type=BAProperties)

	# keymap
	if (not bpy.app.background):
		km, kmi = init_keymaps()
		for k in kmi:
			k.active = True
			addon_keymaps.append((km, k))
	print("loaded Break Apart. num keymaps: " + str(len(addon_keymaps)))


def unregister():
	for cls in classes: bpy.utils.unregister_class(cls)

	# global props
	del bpy.types.Scene.baProps

	# keymap
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()
	print("unloaded Break Apart.")
