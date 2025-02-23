import sys
import datetime
sys.path.insert(0, "..")
from opcua import Client

plc = Client("opc.tcp://192.168.0.1:4840")
plc.connect()
root = plc.get_root_node()
objects = root.get_children()[0]
PLC = objects.get_children()[2]

# output_file = open("IOtrace_" + str(datetime.datetime.now()) + ".txt", "w")
output_file = open("IOtrace.txt", "w")

output_header_line1 = ""
output_header_line2 = ""

# print("\n\npulling out the values of global DB......\n\n")
# print("NAME        TYPE        ")

global_db_info1 = []
global_db_info2 = []
global_db_value = []
global_db_list = []

def get_db_values():
	global global_db_info1, global_db_info2, global_db_value, global_db_list

	for a in global_db_list:
		varValue = a.get_data_value().Value.Value
		global_db_value.append(varValue)


def get_db_info(db):
	global global_db_info1, global_db_info2, global_db_value, global_db_list

	global_db_children_children = db.get_variables()
	for a in global_db_children_children:
		varName = a.nodeid.Identifier[1:-1].replace('"', "").replace(',', "$")
		varType = a.get_data_type_as_variant_type().name

		if varType == "ExtensionObject":
			get_db_info(a)
		else:
			global_db_info1.append(varName)
			global_db_info2.append(varType)

			varValue = a.get_data_value().Value.Value
			global_db_value.append(varValue)
			global_db_list.append(a)

# def clean_header1_line(output_header_line1):
# 	output_header_line1_list = output_header_line1.split(",")
# 	pattern = '([[0-9]+)(,)([0-9]+])'
# 	reCompiler = re.compile(pattern)
# 	for matchedPattern in reCompiler.finditer(output_header_line1):
# 	    mp = matchedPattern.group(1) + matchedPattern.group(2) + matchedPattern.group(3)
# 	    new_mp = matchedPattern.group(1) + "$" + matchedPattern.group(3)
# 	    # print(mp)
# 	    output_header_line1 = output_header_line1.replace(mp, new_mp)

# 	return output_header_line1
	
global_db = PLC.get_children()[13]
global_db_children = global_db.get_children()
global_db_children = global_db_children[1:]

for k in global_db_children:
	get_db_info(k)

output_header_line1 = ",".join(global_db_info1) + ","

# print("\n\npulling out the values of sensors......\n\n")
# print("NAME        TYPE        ")

Inputs = PLC.get_children()[15]
Inputs_children = Inputs.get_children()
Inputs_children = Inputs_children[1:]
for i in Inputs_children:
    output_header_line1 += str(i.nodeid.Identifier[1:-1]) +","

# print("\n\npulling out the values of actuators......\n\n")
# print("NAME        TYPE        ")

Outputs = PLC.get_children()[17]
Outputs_children = Outputs.get_children()
Outputs_children = Outputs_children[1:]
for j in Outputs_children:
    output_header_line1 += str(j.nodeid.Identifier[1:-1]) +","

print(output_header_line1[:-1])
print("\n")
output_file.write(output_header_line1[:-1] + "\n")

# print("\n\npulling out the values of global DB......\n\n")
# print("NAME        TYPE        ")

output_header_line2 = ",".join(global_db_info2) + ","

# print("\n\npulling out the values of sensors......\n\n")
# print("NAME        TYPE        ")

Inputs = PLC.get_children()[15]
Inputs_children = Inputs.get_children()
Inputs_children = Inputs_children[1:]
for i in Inputs_children:
    output_header_line2 += str(i.get_data_type_as_variant_type().name)+ ","

# print("\n\npulling out the values of actuators......\n\n")
# print("NAME        TYPE        ")

Outputs = PLC.get_children()[17]
Outputs_children = Outputs.get_children()
Outputs_children = Outputs_children[1:]
for j in Outputs_children:
    output_header_line2 += str(j.get_data_type_as_variant_type().name)+ ","

print(output_header_line2[:-1])
output_file.write(output_header_line2[:-1] + "\n")

while(True):
	print("===============================")
	t1 = datetime.datetime.now()

	global_db = PLC.get_children()[13]
	global_db_children = global_db.get_children()
	global_db_children = global_db_children[1:]
	output_line = ""
	global_db_info1 = []
	global_db_info2 = []
	global_db_value = []

	get_db_values()
	
	output_line = ",".join([str(x) for x in global_db_value]) + ","

	# print("\n\npulling out the values of sensors......\n\n")
	# print("NAME        TYPE        VALUE")
	
	Inputs = PLC.get_children()[15]
	Inputs_children = Inputs.get_children()
	Inputs_children = Inputs_children[1:]
	for i in Inputs_children:
	    output_line += str(i.get_data_value().Value.Value) + ","
	
	# print("\n\npulling out the values of actuators......\n\n")
	# print("NAME        TYPE        VALUE")

	Outputs = PLC.get_children()[17]
	Outputs_children = Outputs.get_children()
	Outputs_children = Outputs_children[1:]
	for j in Outputs_children:
	    output_line += str(j.get_data_value().Value.Value) + ","

	print(output_line[:-1])
	output_file.write(output_line[:-1] + "\n")
	t2 = datetime.datetime.now()
	print("Time difference between T1 & T2 is: " + str(t2-t1))

output_file.close()
plc.disconnect()

