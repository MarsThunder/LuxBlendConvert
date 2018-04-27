# convert_materials_to_lux.py
# 
# Copyright (C) 5-Apr-2018, by Marshall Flynn
#
# 
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Convert Materials to LuxCore 2.0",
    "author": "Marshall Flynn",
    "version": (1, 7, 0),
    "blender": (2, 79, 0),
    "location": "Properties > Material > Convert Materials to LuxRender",
    "description": "Convert non-nodes Blender Render materials to Lux",
    "warning": "You must have Blender 2.79 and BlendLuxCore Plugin/Addon",
    "support": "COMMUNITY",
    "wiki_url": "http://www.tinkeringconnection.com/wp-content/storage/lux_converter_doc.pdf",
    "category": "Material"}


import bpy
import math
import mathutils
import codecs
from math import log
from math import pow
from math import exp
import os, sys
import logging
import time
import datetime
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
scriptPath = str(os.path.dirname(os.path.realpath(__file__)))

print("Script path: ",scriptPath)



#-----------------------------------------------------------------------
#print ("Sys Path: ", str(sys.path))

def AutoNodeOff():
    bpy.context.scene.render.engine = 'BLENDER_RENDER'
    mats = bpy.data.materials
    for nowmat in mats:
        nowmat.use_nodes = False
        


def AutoNode(active=False):
    print ("This is the Lux Material Converter")
    #---------------------------------------------------------------------
    convert_type = 'cycles'
    active_change = 0
    active_color = (0.6,0.6,0.6)  # same as diff_color for now
    object_name = ''
    diffuse_col = (0.6, 0.6, 0.6)  # Start color
    diffuse_trans = 1
    diffuse_rough = 0.08
    orig_diffuse = None  #this is a bsdf color
    core_shader = 'Diffuse BSDF'
    obj_incr = 0
    face_incr = -1
    object_store = {}
    face_items = []
    material_idx = 0
    matSlot = 0
    has_image = 0
    has_bump = 0
    has_glass = 0
    has_volume = 0
    has_light = 0
    has_normimage = 0
    has_3Dtex = 0
    has_mixRGB = 0
    has_mixshader = 0
    has_emitt = 0
    has_metal = 0
    img_path = ""
    glass_ior = 1.3
    specular_col = (0.3, 0.3, 0.3)
    absorb_col = (0.0, 0.0, 0.0)
    mix4lux1 = (0.1, 0.1, 0.1)
    mix4lux2 = (0.1, 0.1, 0.1)
    mix_share = 0.5
    mixnode1_name = "Nothing"
    mixnode2_name = "Nothing"
    mixnode1_col = (0.3, 0.3, 0.3)
    mixnode2_col = (0.3, 0.3, 0.3)
    shade_portion = 0.5
    lgt_power = 40
    bump_path = ""
    bump_invert = False
    tex_scale = 0.5
    bump_hgt = 0.0002
    Texture3D = "NO_3D"
    lux_3Dnodename = "Nothing"
    #-----------------------------------------------------------------------   
    print ("Starting convert here.....")
    bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene
    if (convert_type == 'cycles'):
        sc.render.engine = 'CYCLES'
        
    if (convert_type == 'blender'):
        sc.render.engine = 'BLENDER_RENDER'
       

    for item in bpy.context.selectable_objects:   
           item.select = False   
  
    outpath = bpy.data.scenes[0].render.filepath
    runstart = time.strftime("%H%M%S")
    startnum = int(time.time())
  
    timestring = str(runstart)
    
    # Log File:
    lpath = outpath + '\log'
    
    

    try:
        os.makedirs(lpath)
    except:
        e = sys.exc_info()[0]
        if e != '':
            print ("OK, Log Folder exists: " + str(e))
            
    lpath = lpath + "//"
    wr = open(lpath + 'LuxConvert' + timestring + '.log', 'a')
    bpy.ops.object.select_all(action='DESELECT')
    wr.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
    wr.write("New Run....\n")
    wr.write("LuxCore 2.0 Converter\n")
    wr.write("  Marshall Flynn, 2018\n")
    wr.write("------------------------------------------------\n")
    wr.write("Started at " + str(runstart) + "\n")
    
    wr.write("Conversion Type: " + convert_type + "\n")
    # Start iterating objects
    # If object normals are messed up, so will the image maps.  This will not correct normals.
    original_stderr = sys.stderr    

    # If there ARE objects selected then act on all objects
    if bpy.context.selected_objects != []:
        print('These are selected:')
        for obj in bpy.context.selected_objects:
            print(obj.name, obj, obj.type)
        if obj.type == 'MESH': 
            print(" OBJECT: ", obj.name)

    odd_material = 'nothing'
    print('---------------------------------------------------')
    # If there are NO objects selected then act on all objects
    if bpy.context.selected_objects == []:
        print('These are not selected:')
        for obj in bpy.context.scene.objects: 
            print(obj.name, obj, obj.type)
            if obj.type == 'MESH': 
                print(" OBJECT: ", obj.name)
                print(" MATERIAL: ", str(obj.data.materials.items()))
            if obj.type == 'LAMP':
                print(" OBJECT: ", obj.name)
                print(" MATERIAL: ", str(obj.data.items()))


    print('---------------------------------------------------')
# Lets get coding!
#----------------------------------------------------------------------
    things = bpy.data.objects
    print("All Objects:")
    for olist in things:
        print(str(olist.name))
    for nowthing in things:
        print('______________________________________________________')
        print('Running Nowthing in Things group:')
        print('Original Active Color: ' + str(active_color))
        print('RAW NOWTHINGS: ' + str(nowthing))
        print('NowThing Type: ', str(nowthing.type))
        if nowthing.type not in {'CAMERA', 'LAMP', 'ARMATURE', 'EMPTY'}:
            
            object_name = str(nowthing.name)
            print ("Iterating Objects - Now on " + str(object_name))
            print ("Object Faces Loop ----------------------------------")
            obj_incr = obj_incr + 1
            
            bi_dimensionX = nowthing.dimensions[0]
            bi_dimensionY = nowthing.dimensions[1]
            bi_area = bi_dimensionX * bi_dimensionY
            
            wr.write(">>>New Object --------------------------------\n")
            wr.write(">>> Supposedly: " + str(object_name) + "\n")
            
            actob = bpy.context.active_object
            print ('Checking the Last Active object......')
            print ("So Active Object is " + str(actob.name))
            mesh = nowthing.data
            
            print ("Current Mesh is: " + str(mesh.name))
           

            
            #print(current_dict)
            bpy.context.scene.objects.active = bpy.data.objects[object_name]
            newactob = bpy.context.scene.objects.active
            
            
            print ("Object Loop Current Object: " + str(object_name))
            print ("Current Object Type is: " + str(nowthing.type))
            print ("Retained Active Object Data -------------------------------------")
            print ("Actual Object Number: ", str(obj_incr))
            #print ("Actual Face Number: ", str(face_incr))
            #print ("Object Faces and Color: ", str(object_store[object_name]))
            print ("  Object Loop Original Technical Active Object: " + str(actob))           
            print ("  Object Loop New Active Object Name: " + str(newactob)) # Not right
            print ("  The untouched Original Diffuse color is: ", str(orig_diffuse))
            try:
                wr.write("Current Object is: " + str(object_name)+ "\n")
                wr.write("Current Object X Dimension: " + str(bi_dimensionX) + "\n")
                wr.write("Current Object Y Dimension: " + str(bi_dimensionY) + "\n")
                wr.write("Current Object Area: " + str(bi_area) + "\n")
                wr.write("Current Object Type is: " + str(nowthing.type)+ "\n")
                    
            except:
                wr.write("We are having Unicode issues!  Check material names....: " + "\n")
                # Maybe bail on this object?

#  Now lets check object Materials--------------------------------------------------------------------------
            for mats in nowthing.material_slots:
                sc.render.engine = 'CYCLES'
                nowmat = mats.material
                wr.write(" NowThing: " + str(nowthing) + "\n")
                nowmat.use_nodes = True
                nodetree = nowmat.node_tree
                nodeLinks = nodetree.links
                
                
                print ("  Nodes Available : %s" %  nodetree.nodes.keys())
                print ("###############################################################################################")
                print ("Material Loop Current Object: " + str(object_name))
                print ("New Material ------------------------------------")
                print ("Raw Loop material: " + str(mats) )
                # wr.write(" Found Diffuse Color: " + str(nowmat.diffuse_color) + "\n")               
                print ("Current Material Index: " + str(material_idx))
                sys.stdout.flush()  #Flush annoying retained text
                print ("Next 3 may not match match.......OK")
                print ("  Loop nowmat is " + nowmat.name)
                if bpy.context.object.active_material:
                   print ("  Technical Active Material is: " + str(bpy.context.active_object.active_material))
                   print ("  Active Material Index: " + str(things[object_name].active_material_index))
                   # print ("Technical Active Node Material is: " + str(nowmat.active_node_material))
                   wr.write(" Current Material: " + mats.material.name + "\n")
                   
                   wr.write(" Active Node Material: " + str(nowmat.active_node_material) + "\n")
                   wr.write(" Active Original Raw Diffuse: " + str(nowmat.diffuse_color) + "\n")
                   wr.write(" Material Slot: " + str(bpy.context.object.material_slots) + "\n")
                   wr.write(" Active Material Index: " + str(things[object_name].active_material_index) + "\n")
                idtype = 'Material'
                # context_data = bpy.context.active_object.active_material
                print ("  ")
                print ("Original Material Details:")
                shader_outnode = nodetree.nodes['Material Output']  # This has to be here for Cycles
                #find out what is connected
                outnode_surface = shader_outnode.inputs[0]
                if outnode_surface.is_linked:
                    srcnode = outnode_surface.links[0].from_node
                    srctype = outnode_surface.links[0].from_node.type
                    srcname = outnode_surface.links[0].from_node.name
                    core_shader = srcname
                    print ("Output Node fed by: ", str(srctype))
                    print (" Which is: ", str(srcname))
                shader_base = nodetree.nodes[srcname]    #Whatever is connected to output
                for inlinks in shader_base.inputs:
                    print ("Shader Base Inputs: ", str(inlinks))
                if srcname == 'Mix Shader':                       #There may be no default color
                    has_mixshader = 1
                    shade_portion = shader_base.inputs[0].default_value
                    mix_shade1 = shader_base.inputs[1]
                    mix_shade2 = shader_base.inputs[2]
                    shade1 = mix_shade1.links[0].from_node.name
                    #test = mix_shade1.links[0].from_node
                    shade2 = mix_shade2.links[0].from_node.name                    
                    mixnode1_name = shade1
                    mixnode2_name = shade2
                    print ("Mix input 1 node: ", str(shade1))
                    print ("Mix input 2 node: ", str(shade2))
                    print("Original Diffuse: ", str(orig_diffuse))
                    mixnode1 = nodetree.nodes.get(shade1)  #this is material input to slot 1
                    mixnode2 = nodetree.nodes.get(shade2)  #this is material input to slot 2
                    for inshade1 in mixnode1.inputs:
                        print ("Mix Shade1 Inputs: ", str(inshade1.name))
                        if inshade1.name == 'Normal':                                        
                            if mixnode1.inputs['Normal'].is_linked:
                                has_bump = 1
                                normbump1 = mixnode1.inputs[2].links[0].from_node.name
                                normnode1 = nodetree.nodes.get(normbump1)
                                if normnode1.inputs['Height'].is_linked:
                                    has_normimage = 1
                    for inshade2 in mixnode2.inputs:
                        print ("Mix Shade2 Inputs: ", str(inshade2.name))
                        if inshade2.name == 'Normal':
                            if mixnode2.inputs['Normal'].is_linked:
                                has_bump = 1
                                normbump2 = mixnode1.inputs[2].links[0].from_node.name
                                normnode2 = nodetree.nodes.get(normbump2)
                                if normnode2.inputs['Height'].is_linked:
                                    has_normimage = 1
                    if mixnode1.inputs[0].is_linked:
                        node1src = mixnode1.inputs[0].links[0].from_node.name
                        node1type = mixnode1.inputs[0].links[0].from_node.type
                        print ("Mix input type: ", str(node1type))
                        if node1type == 'TEX_IMAGE':
                            print("Mix 1 has Text Image....")
                            print ("File is: ", str(mixnode1.inputs[0].links[0].from_node.image.filepath))
                            has_image = 1
                            img_path = mixnode1.inputs[0].links[0].from_node.image.filepath
                    else:
                        mixnode1_col = mixnode1.inputs[0].default_value
                        mixnode1_col = (mixnode1_col[0], mixnode1_col[1], mixnode1_col[2])
                        print ("Mixnode1 Color: ", str(mixnode1_col))
                    if mixnode2.inputs[0].is_linked:
                        node2src = mixnode2.inputs[0].links[0].from_node.name
                        node2type = mixnode2.inputs[0].links[0].from_node.type
                        print ("Mix input type: ", str(node2type))
                        if node2type == 'TEX_IMAGE':
                            print("Mix 2 has Text Image....")
                            print ("File is: ", str(mixnode2.inputs[0].links[0].from_node.image.filepath))
                            has_image = 1
                            img_path = mixnode2.inputs[0].links[0].from_node.image.filepath
                    else:
                        mixnode2_col = mixnode1.inputs[0].default_value
                        mixnode2_col = (mixnode2_col[0], mixnode2_col[1], mixnode2_col[2])
                        print ("Mixnode2 Color: ", str(mixnode2_col))
                                   
                    
                if srcname == 'Diffuse BSDF':
                    shader_color = shader_base.inputs[0]   #NodeSocketColor
                    shader_rough = shader_base.inputs[1]   
                    orig_diffuse = shader_color.default_value
                    diffuse_rough = shader_rough.default_value    #shininess
                    shader_normal = shader_base.inputs['Normal']
                    
                    # grab color input
                    feedcolor = shader_color
                    feednormal = shader_normal
                    print("Base Start Color: ", str(orig_diffuse[:]))
                    print("Rough: ", str(diffuse_rough))
                    #Extract out color and opacity
                    diffuse_col = (orig_diffuse[0], orig_diffuse[1], orig_diffuse[2])
                    print("Extracted RGB Color: ", str(diffuse_col[:]))
                    diffuse_trans = orig_diffuse[3]
                    print("Extracted Transparency: ", str(diffuse_trans))
                    if feedcolor.is_linked:      # What is attached to Diffuse Color
                        srcnode = feedcolor.links[0].from_node
                        srctype = feedcolor.links[0].from_node.type
                        srcname = feedcolor.links[0].from_node.name
                        print("Color From Node Type: ", str(srctype))
                        print ("Color Source Node Name: ", str(srcname))
                        if srctype == 'TEX_IMAGE':
                            print("Text Image from Source")
                            print ("File is: ", str(srcnode.image.filepath))
                            has_image = 1
                            img_path = srcnode.image.filepath
                        elif srctype == 'MIX_RGB':
                            print ("RGB Mix from source")
                            color_mix = nodetree.nodes.get(srcname)
                            mix_color1 = color_mix.inputs[1].default_value
                            mix_color2 = color_mix.inputs[2].default_value
                            mix_share = color_mix.inputs[0].default_value
                            print("Mix Share: ", str(mix_share))
                            print("Mix Color 1: ", str(mix_color1[:]))
                            print("Mix Color 2: ", str(mix_color2[:]))
                            mix4lux1 = (mix_color1[0], mix_color1[1], mix_color1[2])
                            mix4lux2 = (mix_color2[0], mix_color2[1], mix_color2[2])
                            has_mixRGB = 1
                        else:
                            print ("3D texture from source:")
                            Texture3D = str(srctype)
                            print (" ", str(Texture3D))
                            has_3Dtex = 1
                    if feednormal.is_linked:         # What is attached to normal
                        srctype = feednormal.links[0].from_node.type
                        srcnode = feednormal.links[0].from_node
                        srcname = feednormal.links[0].from_node.name
                        print("Normal From Node Type: ", str(srctype))
                        print ("Normal Source Node Name: ", str(srcname))
                        if srctype == 'BUMP':
                            print ("Normal Input is Bump")
                            has_bump = 1
                            bumpnode = nodetree.nodes.get(srcname)
                            print ("Bump Inputs: ", str(bumpnode.inputs))
                            bump_hgt = bumpnode.inputs[2].default_value
                            print ("Bump Height: ", str(bump_hgt))
                            feedbump = bumpnode.inputs[2]   #height
                            bump_invert = bumpnode.invert
                            print ("Bump Invert Value: ", str(bump_invert))
                            if feedbump.is_linked:
                                print ("Direct is direct connection node to bump.....")
                                srctype = feedbump.links[0].from_node.type
                                srcnode = feedbump.links[0].from_node
                                srcname = feedbump.links[0].from_node.name
                                bumptexnode = nodetree.nodes.get(srcname)
                                print ("Bump Height Source: ", str(srcname))
                                feedconvert = bumptexnode.inputs[0]
                                if feedconvert.is_linked:
                                    srctype = feedconvert.links[0].from_node.type
                                    srcnode = feedconvert.links[0].from_node
                                    srcname = feedconvert.links[0].from_node.name
                                    convertnodeimg = nodetree.nodes.get(srcname)
                                    print ("Bump Convert Source Name: ", str(srcname))  
                                    if str(srcname) == "Image Texture":
                                        has_normimage = 1
                                        print ("has_normimage = 1")
                                        print ("Convert Source File is: ", str(srcnode.image.filepath))
                                        bump_path = srcnode.image.filepath
                                    elif str(srcname) != "Image Texture":  # This is your 3D texture
                                        has_3Dtex = 1
                                        tex_scale = convertnodeimg.inputs["Scale"].default_value
                                        print ("Scale: ", str(tex_scale))
                                else:
                                    # We have a bump node with no imput
                                    print ("Bump with no input!")
                    else:
                        has_bump = 0
                    
                    if has_3Dtex != 0:
                        print("Retained 3D Texture Info!")
                        print(" Which is: ", str(Texture3D))
                        if Texture3D == "TEX_VORONOI":
                            print("Setting node name for Lux....")
                            lux_3Dnodename = "LuxCoreNodeTexBlenderVoronoi"
                if srcname == 'Glass BSDF':
                    glass_ior = shader_base.inputs[2].default_value
                    shader_color = shader_base.inputs[0]   #NodeSocketColor
                    orig_diffuse = shader_color.default_value
                    diffuse_col = (orig_diffuse[0], orig_diffuse[1], orig_diffuse[2])
                if srcname == 'Emission':
                    has_emitt = 1
                    shader_color = shader_base.inputs[0]   #NodeSocketColor
                    orig_diffuse = shader_color.default_value
                    feedcolor = shader_color
                    if feedcolor.is_linked:      # What is attached to Diffuse Color
                        srcnode = feedcolor.links[0].from_node
                        srctype = feedcolor.links[0].from_node.type
                        srcname = feedcolor.links[0].from_node.name
                        print("Color From Node Type: ", str(srctype))
                        print ("Color Source Node Name: ", str(srcname))
                        lgt_power = shader_base.inputs[1].default_value
                    else:
                        # We go with original diffuse color
                        diffuse_col = (orig_diffuse[0], orig_diffuse[1], orig_diffuse[2])
                        lgt_power = shader_base.inputs[1].default_value
                if srcname == 'Anisotropic BSDF':
                    has_metal = 1
                    shader_color = shader_base.inputs[0]   #NodeSocketColor
                    orig_diffuse = shader_color.default_value
                    feedcolor = shader_color
                    if feedcolor.is_linked:      # What is attached to Diffuse Color
                        srcnode = feedcolor.links[0].from_node
                        srctype = feedcolor.links[0].from_node.type
                        srcname = feedcolor.links[0].from_node.name
                        print("Color From Node Type: ", str(srctype))
                        print ("Color Source Node Name: ", str(srcname))
                        lgt_power = shader_base.inputs[1].default_value
                    else:
                        # We go with original diffuse color
                        diffuse_col = (orig_diffuse[0], orig_diffuse[1], orig_diffuse[2])
                        diffuse_rough = shader_base.inputs[1].default_value
                
                    
                
                
                
                context_data = nowmat
                

                #Done with input
                
                print ("Inputs done........................")
                #print ("Objects and Faces: ",str(object_store))
                #Now we adjust the variables for Lux
                
#==================================================================================================
                # LuxCore 2.0 section
                from pprint import pprint
                print("LuxCore Section========================================")
                sc.render.engine = 'LUXCORE'
                
                
                nowmat.use_nodes = True
                nowmat.node_tree.nodes.clear()
                # Turn on Node Editor for Lux
                
                for area in bpy.context.screen.areas:
                    if area.type == "NODE_EDITOR":
                        print ("Area type: ", str(area.type))
                        #print (str(dir(area)))
                        for space in area.spaces:
                            if space.type == "NODE_EDITOR":
                                print ("Space type: ", str(space.type))
                                #print (str(dir(space)))
                                #bpy.context.area.type = 'NODE_EDITOR'
                                space.tree_type = 'luxcore_material_nodes'
                
                # material node first becomes Matte
                #Must change to glossy and use roughness like Cycles
                print ("")
                print ("OUTPUT: Creating LUX Materials--------------------------------------")
                print ("")
                # test = nowmat.node_tree
                # for attr in dir(test):
                #     print("test.%s = %r" % (attr, getattr(test, attr)))
                           
                
                matSlot = matSlot + 1
                # We add functions because of traversing upper folders issues with import
                luxmat = bpy.data.materials[nowmat.name]  # OK, this works
                lux_treename = "Nodes_" + luxmat.name
                print ("Lux Material Index: ",str(material_idx))
                print ("Lux Raw Material: ",str(luxmat))
                print ("Lux Material Name: ",str(luxmat.name))
                lux_tree = bpy.data.node_groups.new(name=lux_treename, type="luxcore_material_nodes")
                #init_mat_node_tree(lux_tree)
                lux_tree.use_fake_user = True
                lux_nodes = lux_tree.nodes
                matoutX = 400
                matoutY = 350
                lux_out = lux_nodes.new("LuxCoreNodeMatOutput")
                lux_out.location = matoutX,matoutY
                #lux_matte = lux_nodes.new("LuxCoreNodeMatMatte")
                print ("We are converting from this Cycles shader: ", str(core_shader))
                shader_type = "NoMatchYet"
                if core_shader == 'Diffuse BSDF':                    
                    shader_type = "LuxCoreNodeMatGlossy2"
                if core_shader == 'Glass BSDF':                    
                    shader_type = "LuxCoreNodeMatGlass"
                if core_shader == 'Mix Shader':                    
                    shader_type = "LuxCoreNodeMatMix"
                if core_shader == 'Emission':
                    shader_type = "LuxCoreNodeMatGlossyTranslucent"
                if core_shader == 'Anisotropic BSDF':
                    shader_type = "LuxCoreNodeMatMetal"
                print ("We are replacing with this Lux shader: ", str(shader_type))
                print ("Using this base color: ", str(diffuse_col))
                
                lux_shader = lux_nodes.new(shader_type)  # we get core shader from the Cycles first shader
                matoutX = matoutX - 300
                matoutY = matoutY + 25
                shadelocX = matoutX
                shadelocY = matoutY
                mix1locX = 0
                mix1locY = 0
                lux_shader.location = matoutX, matoutY
                lux_tree.links.new(lux_shader.outputs[0], lux_out.inputs[0])
                luxmat.luxcore.node_tree = lux_tree
                print ("")
                for connect in lux_shader.inputs:
                    print ("Shader Inputs: ", str(connect))
                                
                if shader_type == "LuxCoreNodeMatGlass":
                    lux_shader.inputs['Transmission Color'].default_value = diffuse_col
                    lux_shader.inputs['Roughness'].default_value = diffuse_rough
                    lux_shader.inputs['Opacity'].default_value = diffuse_trans
                if shader_type == "LuxCoreNodeMatGlossy2":
                    lux_shader.inputs[5].default_value = 0.03
                    lux_shader.inputs['Diffuse Color'].default_value = diffuse_col
                    lux_shader.inputs['Roughness'].default_value = diffuse_rough
                    lux_shader.inputs['Opacity'].default_value = diffuse_trans
                if shader_type == "LuxCoreNodeMatGlossyTranslucent":
                    lux_shader.inputs[6].default_value = 0.08         #rough
                    lux_shader.inputs['Diffuse Color'].default_value = diffuse_col
                    lux_shader.inputs[14].default_value = 0.8
                    lux_shader.inputs[1].default_value = diffuse_col
                    if has_emitt != 0:
                        lux_emitt = lux_nodes.new("LuxCoreNodeMatEmission")                        
                        lux_emitt.location = matoutX - 225, matoutY + 30
                        lux_tree.links.new(lux_emitt.outputs[0], lux_shader.inputs['Emission'])
                        lux_shader.inputs[0].default_value = diffuse_col
                        lux_shader.power = lgt_power
                if shader_type == "LuxCoreNodeMatMetal":
                    lux_shader.use_anisotropy = True
                    lux_shader.inputs[0].default_value = diffuse_col
                    lux_shader.inputs[2].default_value = diffuse_rough
                    lux_shader.inputs['Opacity'].default_value = diffuse_trans
                    
                    
                    
                
                if shader_type == "LuxCoreNodeMatMix":
                    mix1locX = shadelocX - 360
                    mix1locY = shadelocX + 475
                    if mixnode1_name == "Glossy BSDF":
                        lux_mix1 = lux_nodes.new("LuxCoreNodeMatGlossy2")                        
                        lux_mix1.location = mix1locX, mix1locY
                        lux_tree.links.new(lux_mix1.outputs[0], lux_shader.inputs['Material 1'])
                    else:
                        lux_shader.inputs['Material 1'].default_value = mixnode1_col
                    if mixnode1_name == "Diffuse BSDF":
                        lux_mix1 = lux_nodes.new("LuxCoreNodeMatMatte")                        
                        lux_mix1.location = mix1locX, mix1locY
                        lux_tree.links.new(lux_mix1.outputs[0], lux_shader.inputs['Material 1'])
                    else:
                        lux_shader.inputs['Material 1'].default_value = mixnode1_col
                    if mixnode1_name == "Translucent BSDF":
                        lux_mix1 = lux_nodes.new("LuxCoreNodeMatGlossyTranslucent")                        
                        lux_mix1.location = mix1locX, mix1locY
                        lux_tree.links.new(lux_mix1.outputs[0], lux_shader.inputs['Material 1'])
                    else:
                        lux_shader.inputs['Material 1'].default_value = mixnode1_col
                    if mixnode1_name == "Emission":
                        lux_mix1 = lux_nodes.new("LuxCoreNodeMatEmission")                        
                        lux_mix1.location = mix1locX, mix1locY
                        lux_tree.links.new(lux_mix1.outputs[0], lux_shader.inputs['Emission'])
                    else:
                        lux_shader.inputs['Material 1'].default_value = mixnode1_col    
                    mix2locX = shadelocX - 360
                    mix2locY = shadelocX + 15
                    if mixnode2_name == "Glossy BSDF":
                        lux_mix2 = lux_nodes.new("LuxCoreNodeMatGlossy2")                        
                        lux_mix2.location = mix2locX, mix2locY
                        lux_tree.links.new(lux_mix2.outputs[0], lux_shader.inputs['Material 2'])
                    else:
                        lux_shader.inputs['Material 2'].default_value = mixnode1_col
                    if mixnode2_name == "Diffuse BSDF":
                        lux_mix2 = lux_nodes.new("LuxCoreNodeMatMatte")                        
                        lux_mix2.location = mix2locX, mix2locY
                        lux_tree.links.new(lux_mix2.outputs[0], lux_shader.inputs['Material 2'])
                    else:
                        lux_shader.inputs['Material 2'].default_value = mixnode2_col
                    if mixnode2_name == "Translucent BSDF":
                        lux_mix2 = lux_nodes.new("LuxCoreNodeMatGlossyTranslucent")                        
                        lux_mix2.location = mix2locX, mix2locY
                        lux_tree.links.new(lux_mix2.outputs[0], lux_shader.inputs['Material 2'])
                    else:
                        lux_shader.inputs['Material 2'].default_value = mixnode2_col
                    if mixnode2_name == "Emission":
                        lux_mix2 = lux_nodes.new("LuxCoreNodeMatEmission")                        
                        lux_mix2.location = mix2locX, mix2locY
                        lux_tree.links.new(lux_mix2.outputs[0], lux_shader.inputs['Emission'])
                    else:
                        lux_shader.inputs['Material 2'].default_value = mixnode2_col   
                    
   
                    
                if has_mixRGB:
                    lux_mixcolor = lux_nodes.new("LuxCoreNodeTexColorMix")
                    matoutX = shadelocX - 300
                    matoutY = shadelocY - 150
                    lux_mixcolor.location = matoutX, matoutY
                    lux_tree.links.new(lux_mixcolor.outputs[0], lux_shader.inputs[0])
                    lux_mixcolor.inputs[3].default_value = mix4lux1
                    lux_mixcolor.inputs[4].default_value = mix4lux2
                    lux_mixcolor.inputs[0].default_value = mix_share
                
                if has_bump != 0:
                    lux_bump = lux_nodes.new("LuxCoreNodeTexBump")
                    matoutX = shadelocX - 300
                    matoutY = shadelocY - 180
                    lux_bump.location = matoutX, matoutY
                    lux_tree.links.new(lux_bump.outputs[0], lux_shader.inputs['Bump'])
                    lux_bump.inputs[1].default_value = bump_hgt
                    lux_bump.inputs[0].default_value = 2.5
                    #Check for invert
                    if bump_invert == True:
                        print("The Bump is inverted!")
                        lux_math = lux_nodes.new("LuxCoreNodeTexMath")
                        matoutX = matoutX - 270
                        matoutY = matoutY - 15
                        lux_math.location = matoutX, matoutY
                        lux_tree.links.new(lux_math.outputs[0], lux_bump.inputs[1])
                        lux_math.inputs[1].default_value = -1
                        lux_math.mode = 'scale'
                    if has_normimage != 0:
                        print("")
                    elif has_3Dtex != 0:
                        # It must have a 3D texture then
                        print ("This bump is 3D texture based!")
                        print ("Node name: ", lux_3Dnodename)
                        lux_3D = lux_nodes.new(lux_3Dnodename)
                        if Texture3D == "TEX_VORONOI":
                            lux_3D.noise_size = 0.20
                        matoutX = matoutX - 300
                        matoutY = matoutY + 200
                        print ("Loc: ", str(matoutX), str(matoutY))
                        lux_3D.location = matoutX, matoutY
                        if bump_invert == True:
                            lux_tree.links.new(lux_3D.outputs[0], lux_math.inputs[0])
                            lux_tree.links.new(lux_3D.outputs[0], lux_shader.inputs[0])
                        else:    
                            lux_tree.links.new(lux_3D.outputs[0], lux_bump.inputs[1])
                            lux_tree.links.new(lux_3D.outputs[0], lux_shader.inputs[0])
                        lux_bump.inputs[0].default_value = 0.10
                    
                if has_image != 0:
                    lux_image = lux_nodes.new("LuxCoreNodeTexImagemap")
                    if has_bump:
                        matoutX = matoutX - 300
                        
                    else:
                        matoutX = matoutX - 10
                        matoutY = matoutY + 230
                    if has_mixshader:
                        imglocX = mix1locX - 360
                        imglocY = mix1locY - 20
                        lux_image.location = imglocX, imglocY
                        lux_tree.links.new(lux_image.outputs[0], lux_mix1.inputs[0])
                        lux_tree.links.new(lux_image.outputs[0], lux_mix2.inputs[0])
                        print ("For Mix Image...using ", str(img_path))
                        lux_image.filename = img_path
                        lux_image.inputs[0].default_value = 2.5   #gamma
                        lux_image.inputs[1].default_value = 1.15  #brightness
                        try:
                            newimg = bpy.data.images.load(filepath = img_path)
                            lux_image.image = newimg
                        except:
                            e = sys.exc_info()[0]
                            print ("Image Map Error: " + str(e))
                            wr.write("  Image Map Error: " + str(e) + "\n")
                            wr.write("  Most likely bad filepath!! " + "\n")
                        if has_normimage != 0:
                            lux_tree.links.new(lux_image.outputs[0], lux_bump.inputs[1])
                            lux_bump.inputs[0].default_value = 18
                    else:
                        lux_image.location = matoutX, matoutY
                        lux_tree.links.new(lux_image.outputs[0], lux_shader.inputs['Diffuse Color'])
                        lux_image.filename = img_path
                        lux_image.inputs[0].default_value = 2.5   #gamma
                        lux_image.inputs[1].default_value = 1.15  #brightness
                        try:
                            newimg = bpy.data.images.load(filepath = img_path)
                            lux_image.image = newimg
                        except:
                            e = sys.exc_info()[0]
                            print ("Image Map Error: " + str(e))
                            wr.write("  Image Map Error: " + str(e) + "\n")
                            wr.write("  Most likely bad filepath!! " + "\n")
                        if has_normimage != 0:
                            lux_tree.links.new(lux_image.outputs[0], lux_bump.inputs[1])
                            lux_bump.inputs[0].default_value = 18
                # test = lux_tree
                # print ("lux_tree:")
                # 
                # for attr in dir(test):
                #     print("test.%s = %r" % (attr, getattr(test, attr)))
                
                
                
                
                
                
                material_idx = material_idx + 1
            # Reset variables for each material    
            material_idx = 0
            bump_invert = False
            has_3Dtex = 0
            has_normimage = 0
            has_bump = 0
            has_image = 0
            has_normimage = 0
            has_mixRGB = 0
            mix_share = 0.5
            has_mixshader = 0
            has_emitt = 0
            has_metal = 0
            orig_diffuse = None
            diffuse_col = (0.7, 0.7, 0.7)
            
                
                



#-----------------------------------------------------------------------
#-----------------------------------------------------------------------




class cvrtLux(bpy.types.Operator):
    bl_idname = "lux.convert"
    bl_label = "Convert All Materials"
    bl_description = "Convert all materials in the scene from non-nodes to Lux"
    bl_register = True
    bl_undo = True

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        AutoNode(False)
        return {'FINISHED'}
    


from bpy.props import *
sc = bpy.types.Scene
sc.EXTRACT_ALPHA = BoolProperty(attr="EXTRACT_ALPHA", default=False)
sc.EXTRACT_PTEX = BoolProperty(attr="EXTRACT_PTEX", default=False)

class ErrorHandler:

    def __init__(self):
        pass

    def write(self, string):
        errorpath = bpy.data.scenes[0].render.filepath
        errorpath = errorpath + '/log' + '//'
        logit = errorpath + 'BLPython.log'
        # write error to console
        print(string)

        # write error to file
        
        handler = open(logit, "w")
        handler.write(string)
        handler.close()


    
class OBJECT_PT_sceneall(bpy.types.Panel):
    bl_label = "Convert Materials to LuxCore 2.0"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    
    
    def loadup():
        rsource = [
        ("C", "Cycles", "Convert Cycles"),
        ("B", "Blender Internal", "Convert Blender Render")
       ]
        bpy.types.Scene.radio = bpy.props.EnumProperty(name="Input", items=rsource, options = {"ENUM_FLAG"})
        print("OK.  Loadup function run....")
    
    loadup() 
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        
        layout.label("Type of Conversion:")
        layout.prop(sc, "radio", expand=True)
        
        if sc.radio == {'C'}:
            convert_type = 'cycles'
        if sc.radio == {'B'}:
            convert_type = 'blender'
         
        layout.operator("lux.convert", text='Convert Now')  
        


def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()


class Hold_for_Later():
        def dingleberry():
                #Running over faces.....not sure if necessary
            active_change = 1
            if active_change < 1:
                for f in mesh.polygons:  # iterate over faces
                    #print("Current Focus Object: " + str(mesh.name), "Face Num: " + str(f.index), "Material Index; " + str(f.material_index))
                    slot = nowthing.material_slots[f.material_index]                    
                    mater = slot.material
                    
                    if (convert_type == 'cycles'):
                        #print("We are converting from Cycles")
                        
                        mater.use_nodes = True
                        nodetree = mater.node_tree
                        nodeLinks = nodetree.links
                        shader_diffuse = nodetree.nodes["Diffuse BSDF"]    #ShaderNodeBsdfDiffuse
                        shader_color = shader_diffuse.inputs[0]            #NodeSocketColor
                        orig_diffuse = shader_color.default_value
                        
                        
                        if orig_diffuse != None:
                            # grab color input
                            feedin = shader_color                           
                            #print("Base Color: ", str(diffuse_col[:]))
                            if feedin.is_linked:
                                srctype = feedin.links[0].from_node.type
                                srcname = feedin.links[0].from_node.name
                                if srctype == 'TEX_IMAGE':
                                    print("Text Image from Source")
                                if srctype == 'MIX_RGB':
                                    print ("RGB Mix from source")
                                    color_mix = nodetree.nodes.get(srcname)
                                    mix_color1 = color_mix.inputs[1].default_value
                                    mix_color2 = color_mix.inputs[2].default_value
                                    #print("Mix Color 1: ", str(mix_color1[:]))
                                    #print("Mix Color 2: ", str(mix_color2[:]))
                        
                        # I'm not sure we need to traverse faces.  Info held in materials and material IDs
                    if mater is not None and active_change < 1:   #just print on first face
                        
                        #print('Change: ' + str(active_change))
                        active_name = bpy.context.object.name

                        wr.write(" WARNING!!!! Original Active color changed! " + "\n")
                    #-------------------------------------------------------
                    #  populate globals from faces
                    face_items.append(f.index)
                    face_items.append(diffuse_col[:])
                    
                        
                    #-------------------------------------------------------

                    
                    
            face_incr = f.index
            object_store[object_name] = face_items



