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
#  1.00     2025-05-27  JS     -Introduction                                               *
#  2.00     2025-05-28  JS     -Add func processing elements ConditionsForContinue,        *
#                               ReplaceConst                                               *
#*******************************************************************************************
# Import
#*******************************************************************************************
import os
import re
import shutil
import glob
from termcolor import colored, cprint
import json
import xml.etree.ElementTree as ET
import string
import stat
string.ascii_low_and_upp = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


#*******************************************************************************************
# Global Variables
#*******************************************************************************************

#*******************************************************************************************
# Konstants
#*******************************************************************************************
LOCAL_PATH='C:\\temp\\__Python\\'


#*******************************************************************************************
# Functions
#*******************************************************************************************
def force_remove_readonly(dir):
    dir = dir.replace('\\', '/')
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
        path_to_create = ''.join([target_path, dir.get("name"), "\\"])
        print(path_to_create)
        os.makedirs(path_to_create)
        if len(dir):
            create_folder_structure(dir,path_to_create)

def colect_copy_data(config_file_path):
    copy_data = {}

    # parse an xml file by name
    xml_obj = ET.parse(config_file_path)
    copy_data["main_node"] = xml_obj.getroot()

    # gain and test source drive
    source_drive_elem = copy_data["main_node"].find("SourceDrive")
    if (source_drive_elem is None):
        source_drive_elem = copy_data["main_node"].find("Drive")
    if (source_drive_elem is not None):
        if (source_drive_elem.text is None):
            source_drive = input("Source drive was not found in config file. Please enter the Source drive:")
        else:
            if (source_drive_elem.text in string.ascii_low_and_upp):
                source_drive = source_drive_elem.text
            else:
                source_drive = input("Source drive was not found in config file. Please enter the Source drive:")
    else:
        source_drive = input("Source drive was not found in config file. Please enter the Source drive:")
    if (not (":" in str(source_drive))):
        source_drive = source_drive + ":"
    if (os.path.exists(source_drive)):
        copy_data["source_drive"] = source_drive
    else:
        print("Source drive does not exist.")
        cprint("Script stoped",'red')
        exit()

    #Check for ConditionsForContinue
    cond_for_continue = copy_data["main_node"].find("ConditionsForContinue")
    if (cond_for_continue is not None):
        for cond_item in cond_for_continue:
            check_path = cond_item.get("path")
            if (not (":" in str(check_path))):
                check_path = ''.join([copy_data["source_drive"], check_path])
            if (not os.path.exists(check_path)):
                print("Condition does not exist: ", check_path)
                cprint("Script stoped. Fulfill the condition or delete condition form xml config file. ", 'red')

    # **** Block replace const in config file ****
    # read input file
    f = open(config_file_path, "rt")
    # read file contents to string
    data = f.read()
    # close the input file
    f.close()

    # replace all const read listed in xml config file
    replace_const = copy_data["main_node"].find("ReplaceConst")
    if (replace_const is not None):
        for replace_item in replace_const:
            replace_item_const = replace_item.get("xml_const")
            replace_item_value = replace_item.get("value")
            # replace all occurrences of the required string in string data read from config file
            # data = data.replace("#SW_NAME#", "ABCD")
            data = data.replace(replace_item_const, replace_item_value)

    # replace all const read from file
    replace_const = copy_data["main_node"].find("ReadReplaceConst")
    if (replace_const is not None):
        for replace_item in replace_const:
            replace_item_path = replace_item.get("path")
            if (not (":" in str(replace_item_path))):
                replace_item_path = ''.join([copy_data["source_drive"], replace_item_path])
            f = open(replace_item_path, "rt")
            repplace_item_data = f.read()
            f.close()
            replace_item_regex = replace_item.get("regex")
            replace_item_value = re.search(replace_item_regex, repplace_item_data).group(1)
            replace_item_const = replace_item.get("xml_const")
            # replace all occurrences of the required string in string data read from xml config file
            # data = data.replace("#SW_NAME#", "ABCD")
            data = data.replace(replace_item_const, replace_item_value)

    #gain again xml object data
    xml_obj = ET.fromstring(data)
    #store xml dato into copy_data["main_note"]
    copy_data["main_node"] = xml_obj

    # gain and test target path
    target_path_elem = copy_data["main_node"].find("TargetPath")
    if (target_path_elem is None):
        target_path_elem = copy_data["main_node"].find("DeliveryPath")
    if (target_path_elem is None):
        target_path = input("TargetPath was not found in config file. Please enter the TargetPath:")
    else:
        target_path = target_path_elem.text
    drive_tail = os.path.splitdrive(target_path)
    if (drive_tail[0] == ""):
        target_path = source_drive + target_path
    drive_tail = os.path.splitdrive(target_path)
    print("Drive of path '%s':" %target_path, drive_tail[0])
    print("Tail of path '%s':" %target_path, drive_tail[1])
    print(target_path)
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
            print("TargetPath does not exist.")
            cprint("Script stoped",'red')
            exit()

    return copy_data

def perform_copy(copy_data):
    #For debug you can use following command:
    #print (ET.dump(copy_data["main_node"]))

    #Prepare output dir
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
                cprint("Script stoped", 'red')
                exit()
    os.makedirs(target_path)

    #Create folder structure if requested
    xml_sub_directories = copy_data["main_node"].find("DeliveryPathSubDirs")
    if (xml_sub_directories is not None):
      create_folder_structure(xml_sub_directories,target_path)

    #Start copy sequence
    build_output = copy_data["main_node"].find("BuildOutput").get("path")
    copy_set = copy_data["main_node"].find("CopySet")
    for where in copy_set:
        var_where = ''.join([copy_data["target_path"], where.get("name")])
        if (not ("." in str(var_where))):
            if ((str(var_where)[-1]) != "\\"):
                var_where = ''.join([str(var_where), "\\"])
        #add test if there is file name in where element
        print(var_where)
        for item in where:
            var_what = item.get("what")
            if "path" in item.attrib:
                if (item.get("path") == "BuildOutput"):
                    var_what = ''.join([copy_data["source_drive"], build_output, var_what])
            if (not (":" in str(var_what))):
                var_what = ''.join([copy_data["source_drive"], var_what])
            if os.path.isdir(var_what):
                if (os.path.exists(var_where)):
                    force_remove_readonly(var_where)
                # copy all subdirs recursively
                shutil.copytree(var_what, var_where)
            else:
                # pattern1 = '*.txt'
                # matching_filenames_1 = glob.glob(pattern1)
                # ['file1.txt', 'file2.txt', 'file3.txt']
                matching_filenames = glob.glob(var_what)
                for item_2 in matching_filenames:
                    # shutil.copy2('src_file.txt', 'dest_file.txt')
                    var_what = item_2
                    print("what: ", var_what)
                    #shutil.copy2(var_what, var_where)
                    if os.path.isdir(var_what):
                        # copy all subdirs recursively
                        var_where_sub = var_where + os.path.basename(item_2)
                        shutil.copytree(var_what, var_where_sub)
                        var_where_sub = ""
                    else:
                        if (not(item.get("file") == "rename")):
                            os.makedirs(var_where, exist_ok=True)
                        shutil.copy2(var_what, var_where)

# #*******************************************************************************************
# Main
# #*******************************************************************************************
current_folder = os.getcwd()
#print('getcwd:      ', os.getcwd())
defaul_config_file_path = os.path.normpath(current_folder+"\\Configs\\CopyToDeliveryExampleConfig.xml")
config_file_path = input("Please enter path to xml config file ["+str(defaul_config_file_path)+"]:")
if (config_file_path == ""):
    config_file_path = defaul_config_file_path
print(config_file_path)
#collect and test input data
copy_data = colect_copy_data(config_file_path)
#perform copy
perform_copy(copy_data)

