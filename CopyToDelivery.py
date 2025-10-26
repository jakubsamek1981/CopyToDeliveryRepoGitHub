#*******************************************************************************************
#              A U T H O R   I D E N T I T Y                                               *
#*******************************************************************************************
# Initials    Name                                                                         *
# --------    ---------------------                                                        *
# JS          Jakub Samek                                                                  *
#*******************************************************************************************
#              R E V I S I O N   H I S T O R Y                                             *
# .HISTORY                                                                                 *
#  Version  Date      Author  Comment                                                      *
#  1.0 - Introduction (basic copy functions, ready for windows and linux systems)
# .PLAN
#  2.0 - Replace const
#  3.0 - Add zip files
#  4.0 - Log messages
#*******************************************************************************************
# Import
#*******************************************************************************************
import os
import shutil
import glob
import xml.etree.ElementTree as ET
import string
import stat
import platform

#***************************************************************************************************
# Global Variables
#***************************************************************************************************
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# ***************************************************************************************************
# Konstants
# ***************************************************************************************************


#***************************************************************************************************
# Functions
#***************************************************************************************************
def force_remove_readonly(dir):
    dir = dir.replace('\\', '/') if IS_WINDOWS else dir
    if (os.path.isdir(dir)):
        for p in os.listdir(dir):
            force_remove_readonly(os.path.join(dir, p))
        if (os.path.exists(dir)):
            os.chmod(dir, stat.S_IWRITE)
            os.rmdir(dir)
    else:
        if (os.path.exists(dir)):
            os.chmod(dir, stat.S_IWRITE)
            os.remove(dir)

def create_folder_structure(xml_directory,target_path):
    for dir in xml_directory:
        path_to_create = os.path.normpath(target_path + dir.get("name"))
        print(path_to_create)
        os.makedirs(path_to_create)
        if len(dir):
            create_folder_structure(dir,path_to_create)

def colect_copy_data(config_file_path):
    copy_data = {}

    # parse an xml file by name
    xml_obj = ET.parse(config_file_path)
    copy_data["main_node"] = xml_obj.getroot()

    # gain and test target path
    script_start_dir = os.getcwd()
    target_path_elem = copy_data["main_node"].find("DeliveryPath")
    if (target_path_elem is None):
        target_path = input("DeliveryPath was not found in config file. Please enter the DeliveryPath:")
    else:
        if (target_path_elem.get("path_type") == "relative"):
            target_path = os.path.normpath(script_start_dir + target_path_elem.text.strip())
        else:
            target_path = target_path_elem.text.strip()

    if (os.path.exists(target_path)):
        copy_data["target_path"] = target_path
    else:
        # CreateIfNotExist
        create_delivery = copy_data["main_node"].find("CreateIfNotExist")
        if (create_delivery is not None):
            if (create_delivery.text == "yes"):
                print("Creating target path:", create_delivery)
                os.makedirs(target_path)
        if (os.path.exists(target_path)):
            copy_data["target_path"] = target_path
        else:
            print("DeliveryPath does not exist.")
            print("!!! Script stoped !!!")
            exit()

    return copy_data

def perform_copy(copy_data):
    # For debug you can use following command:
    # print (ET.dump(copy_data["main_node"]))

    # Prepare output dir
    target_path = copy_data["target_path"]
    if (os.path.exists(target_path)):
        delete_if_exist = copy_data["main_node"].find("DeleteIfExist")
        if (delete_if_exist.text == "yes"):
            force_remove_readonly(target_path)
        else:
            delete_if_exist = input("Target directory already exist do you want to delete it?[y]: ")
            if delete_if_exist in ["y", ""]:
                #os.chmod(target_path, stat.S_IWRITE)
                #os.unlink(target_path)
                #shutil.rmtree(target_path, ignore_errors = True)
                #clear_dir(target_path)
                force_remove_readonly(target_path)
            else:
                print("!!! Script stoped !!!")
                exit()
    os.makedirs(target_path)

    # Create folder structure if requested
    xml_sub_directories = copy_data["main_node"].find("DeliveryPathSubDirs")
    if (xml_sub_directories is not None):
      create_folder_structure(xml_sub_directories,target_path)

    # Start copy sequence
    copy_set = copy_data["main_node"].find("CopySet")
    for where in copy_set:
        if (where.get("path_type") == "relative"):
            # var_where = ''.join([script_start_dir, where.text])
            # .strip() function must be used do read xml element text to remove whitespaces "\n"
            var_where = os.path.normpath(target_path + (where.text.strip()))
        elif(where.get("path_type") == "absolute"):
            var_where = os.path.normpath(where.text.strip())
        else:
           print(where.text)
           print("parameter path_type does not exist")
        # test if target path exist
        if (not (where.get("copy_type") == "rename")):
            if (os.path.exists(var_where)):
                print(var_where)
            else:
                print(var_where)
                print("target path does not exist")
        # loop through items in where element
        for item in where:
            var_what = item.text.strip()
            if "path_type" in item.attrib:
                if item.get("path_type") == "relative":
                    if (item.get("path_type") == "relative"):
                        var_what = os.path.normpath(script_start_dir + item.text.strip())
                    else:
                        var_what = os.path.normpath(item.text.strip())
            if os.path.isdir(var_what):
                if (os.path.exists(var_where)):
                    force_remove_readonly(var_where)
                # copy all subdirs recursively
                shutil.copytree(var_what, var_where)
            else:
                # pattern1 = '*.txt'
                # matching_filenames_1 = glob.glob(pattern1)
                # ['file1.txt', 'file2.txt', 'file3.txt']
                matching_filenames = glob.glob(os.path.normpath(var_what))
                if matching_filenames==[]:
                    print("Error source path does not exist: ", var_what)
                else:
                    for item_2 in matching_filenames:
                        # shutil.copy2('src_file.txt', 'dest_file.txt')
                        var_what = item_2
                        print("WhatSourceItem: ", var_what)
                        # shutil.copy2(var_what, var_where)
                        if os.path.isdir(var_what):
                            # copy all subdirs recursively
                            var_where_sub = var_where + os.path.basename(item_2)
                            shutil.copytree(var_what, var_where_sub)
                            var_where_sub = ""
                        else:
                            if (not(where.get("copy_type") == "rename")):
                                if (os.path.exists(var_what)):
                                    os.makedirs(var_where, exist_ok=True)
                                    shutil.copy2(var_what, var_where)
                                else:
                                    print("Error source path does not exist: ", var_what)
                            else:
                                shutil.copy2(var_what, var_where)

# ***************************************************************************************************
# Main
# ***************************************************************************************************
script_start_dir = os.getcwd()
#print('getcwd:      ', os.getcwd())

#defaul_config_file_path = os.path.normpath(current_folder+"\\Configs\\CopyToDeliveryExampleConfig.xml")
# os.path.join will automatically use \ on Windows and / on Unix.
#defaul_config_file_path = os.path.join(current_folder, "Configs", "CopyToDeliveryExampleConfig_windows.xml")
#defaul_config_file_path = ''.join([current_folder, "/Configs", "/CopyToDeliveryExampleConfig_linux.xml"])

defaul_config_file_path = os.path.normpath(script_start_dir+"/Configs/CopyToDeliveryExampleConfig_windows.xml")
#defaul_config_file_path = os.path.normpath(script_start_dir+"/Configs/CopyToDeliveryExampleConfig_linux.xml")

config_file_path = input("Please enter path to xml config file ["+str(defaul_config_file_path)+"]:")
if (config_file_path == ""):
    config_file_path = defaul_config_file_path
print(config_file_path)
#collect and test input data
copy_data = colect_copy_data(config_file_path)
#perform copy
perform_copy(copy_data)

