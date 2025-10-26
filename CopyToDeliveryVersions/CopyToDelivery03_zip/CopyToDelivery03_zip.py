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
#  2.0 - Replace const
#  3.0 - Add zip files
# .PLAN
#  4.0 - Log messages
#*******************************************************************************************
# Import
#*******************************************************************************************
import os
import re
import shutil
import glob
import xml.etree.ElementTree as ET
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

    # Check for ConditionsForContinue
    cond_for_continue = copy_data["main_node"].find("ConditionsForContinue")
    if (cond_for_continue is not None):
        for cond_item in cond_for_continue:
            check_path = cond_item.text.strip()
            if (cond_item.get("path_type") == "relative"):
                # var_where = ''.join([script_start_dir, where.text])
                # .strip() function must be used do read xml element text to remove whitespaces "\n"
                check_path = os.path.normpath(script_start_dir + (cond_item.text.strip()))
            if (not os.path.exists(check_path)):
                print("Condition does not exist: ", check_path)
                print("Script stoped. Fulfill the condition or delete condition form xml config file. ")

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
            # data = data.replace("#VARIANT", "var456")
            data = data.replace(replace_item_const, replace_item_value)

    # replace all const read from file
    replace_const = copy_data["main_node"].find("ReadReplaceConst")
    if (replace_const is not None):
        for replace_item in replace_const:
            replace_item_path = replace_item.text.strip()
            if (replace_item.get("path_type") == "relative"):
                # var_where = ''.join([script_start_dir, where.text])
                # .strip() function must be used do read xml element text to remove whitespaces "\n"
                replace_item_path = os.path.normpath(script_start_dir + (replace_item.text.strip()))
            if (not os.path.exists(replace_item_path)):
                print("Replace item path does not exist.")
                print("!!! Script stoped !!!")
                exit()
            f = open(replace_item_path, "rt")
            repplace_item_data = f.read()
            f.close()
            replace_item_regex = replace_item.get("regex")
            replace_item_value = re.search(replace_item_regex, repplace_item_data).group(1)
            replace_item_const = replace_item.get("xml_const")
            # replace all occurrences of the required string in string data read from xml config file
            # data = data.replace("#SW_NAME#", "ABCD")
            data = data.replace(replace_item_const, replace_item_value)

    # gain and test zip7z program path
    zip_path_elem = copy_data["main_node"].find("PathToZip")
    if (zip_path_elem is None):
        zip_path = input("PathToZip was not found in config file. Please enter the PathToZip:")
    else:
        zip_path = zip_path_elem.text.strip()
    if (zip_path_elem.get("path_type") == "relative"):
        zip_path = os.path.normpath(script_start_dir + zip_path_elem.text.strip())
    else:
        zip_path = zip_path_elem.text.strip()
    if (os.path.exists(zip_path)):
        copy_data["zip_path"] = zip_path
    else:
        print("PathToZip does not exist. Script stoped")
        exit()

    # gain and test temp path
    temp_path_elem = copy_data["main_node"].find("PathToTemp")
    if (temp_path_elem is None):
        temp_path = input("PathToTemp was not found in config file. Please enter the PathToTemp:")
    else:
        temp_path = temp_path_elem.text.strip()
    if (temp_path_elem.get("path_type") == "relative"):
        temp_path = os.path.normpath(script_start_dir + temp_path_elem.text.strip())
    else:
        temp_path = temp_path_elem.text.strip()
    if (os.path.exists(temp_path)):
        copy_data["temp_path"] = temp_path
    else:
        os.makedirs(temp_path)
        if (os.path.exists(temp_path)):
            copy_data["temp_path"] = temp_path
            print("PathToTemp created")
        else:
            print("PathToTemp does not exist and it is not possible to create it")
            exit()


    # parse xml data
    xml_obj = ET.fromstring(data)
    copy_data["main_node"] = xml_obj

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
                print("target path does not exist:", var_where)
        # loop through items in where element
        for item in where:
            var_what = item.text.strip()
            if "path_type" in item.attrib:
                if item.get("path_type") == "relative":
                    if (item.get("path_type") == "relative"):
                        var_what = os.path.normpath(script_start_dir + item.text.strip())
                    else:
                        var_what = os.path.normpath(item.text.strip())

            zipfile_path_delivery = ""
            # firt test of .zip at the end of the path. In that case it is normal file as each other
            if not ((var_what[-4:] == ".zip") or (var_what[-5:] == ".zipx") or (var_what[-3:] == ".7z")):
                # second test of .zip in the path. In that case zip needs to be unpacked
                if ((".zip" in str(var_what)) or (".7z" in str(var_what))):

                    # Prepare unzip_temp_path dir
                    unzip_temp_path = copy_data["temp_path"]
                    if (os.path.exists(unzip_temp_path)):
                        force_remove_readonly(unzip_temp_path)
                    os.makedirs(unzip_temp_path)

                    zipapp_path = copy_data["zip_path"]

                    if (".zipx" in str(var_what)):
                        zipindex = var_what.index(".zipx")
                        #var_what[:(zipindex)] takes characters from the beginning up to (but not including) zipindex
                        zipfile_path = var_what[:(zipindex + 5)]
                        # var_what[(zipindex):] takes characters from zipindex to the end
                        zipfile_path_rest = var_what[(zipindex + 6):]
                        if IS_WINDOWS:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[2:-5] + "\\"
                        if IS_LINUX:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[:-5] + "/"
                    elif (".7z" in str(var_what)):
                        zipindex = var_what.index(".7z")
                        zipfile_path = var_what[:(zipindex + 3)]
                        zipfile_path_rest = var_what[(zipindex + 4):]
                        if IS_WINDOWS:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[2:-3] + "\\"
                        if IS_LINUX:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[:-3] + "/"
                    else:
                        zipindex = var_what.index(".zip")
                        zipfile_path = var_what[:(zipindex + 4)]
                        zipfile_path_rest = var_what[(zipindex + 5):]
                        if IS_WINDOWS:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[2:-4] + "\\"
                        if IS_LINUX:
                            unzip_temp_path = copy_data["temp_path"] + zipfile_path[:-4] + "/"
                    new_unziped_file_path = unzip_temp_path + zipfile_path_rest
                    # print(zipfile_path)
                    # print(new_unziped_file_path)
                    if (not os.path.exists(unzip_temp_path)):
                        if IS_WINDOWS:
                            my_os_command = zipapp_path + " x " + zipfile_path + " -o" + unzip_temp_path + " -r"
                            os.system(my_os_command)
                        if IS_LINUX:
                            my_os_command = zipapp_path + " x " + zipfile_path + " -o" + unzip_temp_path
                            os.system(my_os_command)
                    var_what = new_unziped_file_path

            # pattern1 = '*.txt'
            # matching_filenames_1 = glob.glob(pattern1)
            # ['file1.txt', 'file2.txt', 'file3.txt']
            matching_filenames = glob.glob(os.path.normpath(var_what))
            if matching_filenames==[]:
                print("Error source path does not exist: ", var_what)
            else:
                for item_2 in matching_filenames:
                    # shutil.copy2('src_file.txt', 'dest_file.txt')
                    var_what2 = item_2
                    print("WhatSourceItem: ", var_what2)
                    # shutil.copy2(var_what, var_where)
                    if os.path.isdir(var_what2):
                        # copy all subdirs recursively
                        # remove asterix if exist
                        if var_what[-1:] == "*":
                            var_what = var_what[:-1]
                        # path subraction final target path = delivery path + (longer - shorter)
                        if IS_WINDOWS:
                            var_where_sub = var_where + "\\" + item_2[len(var_what):]
                        if IS_LINUX:
                            var_where_sub = var_where + "/" + item_2[len(var_what):]
                        if (os.path.exists(var_where_sub)):
                            force_remove_readonly(var_where_sub)
                        shutil.copytree(var_what2, var_where_sub)
                        var_where_sub = ""
                    else:
                        if (not(where.get("copy_type") == "rename")):
                            if (os.path.exists(var_what2)):
                                os.makedirs(var_where, exist_ok=True)
                                shutil.copy2(var_what2, var_where)
                            else:
                                print("Error source path does not exist: ", var_what2)
                        else:
                            shutil.copy2(var_what2, var_where)

# ***************************************************************************************************
# Main
# ***************************************************************************************************
script_start_dir = os.getcwd()
#print('getcwd:      ', os.getcwd())

#defaul_config_file_path = os.path.normpath(current_folder+"\\Configs\\CopyToDeliveryExampleConfig.xml")
# os.path.join will automatically use \ on Windows and / on Unix.
#defaul_config_file_path = os.path.join(current_folder, "Configs", "CopyToDeliveryExampleConfig_windows.xml")
#defaul_config_file_path = ''.join([current_folder, "/Configs", "/CopyToDeliveryExampleConfig_linux.xml"])

#default_config_file_path = os.path.normpath(script_start_dir+"/Configs/CopyToDeliveryExampleConfig_windows.xml")
default_config_file_path = os.path.normpath(script_start_dir+"/Configs/CopyToDeliveryExampleConfig_linux.xml")

config_file_path = input("Please enter path to xml config file ["+str(default_config_file_path)+"]:")
if (config_file_path == ""):
    config_file_path = default_config_file_path
print(config_file_path)
#collect and test input data
copy_data = colect_copy_data(config_file_path)
#perform copy
perform_copy(copy_data)