"""
from pysnmp.entity.rfc3413.oneliner import cmdgen

cmdGen = cmdgen.CommandGenerator()

errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.CommunityData('public'),
    cmdgen.UdpTransportTarget(('192.168.90.103', 161)),
    '1.0.8802.1.1.2.1.3.7',
)

if errorIndication:
    print(errorIndication)
else:
    if errorStatus:
        print('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
            )
        )
    else:
        size = (int)(len(varBindTable)/3)
        index = 0
        name, val = "" , ""
        if(size > 0):
            while(start < size):
                print(varBindTable[start+3][0][1].prettyPrint())
                print(varBindTable[start+6][0][1].prettyPrint())
                start += 1
        else:
            pass
        #print(varBindTable[1][0][1])
        
        for varBindTableRow in varBindTable:
            for name, val in varBindTableRow:
                print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
                pass

"""

"""
from pysnmp.entity.rfc3413.oneliner import cmdgen

SNMP_HOST = '192.168.90.104'
SNMP_PORT = 161
SNMP_COMMUNITY = 'public'

cmd_generator = cmdgen.CommandGenerator()

#error_notify, error_status, error_index, var_binds = cmd_generator.getCmd(cmdgen.CommunityData(SNMP_COMMUNITY),cmdgen.UdpTransportTarget((SNMP_HOST, SNMP_PORT)),cmdgen.MibVariable('SNMPv2-MIB', 'sysDescr', 0),lookupNames=True, lookupValues=True)
error_notify, error_status, error_index, var_binds = cmd_generator.getCmd(cmdgen.CommunityData(SNMP_COMMUNITY),cmdgen.UdpTransportTarget((SNMP_HOST, SNMP_PORT)),'1.0.8802.1.1.2')
if error_notify:
    print(error_notify)
elif error_status:
    print(error_status)
else:
    for name, val in var_binds:
        print('%s = %s' % (name.prettyPrint(),val.prettyPrint()))
"""
"""
keyTest = bytes('dpid:0000000000000001', encoding='utf-8')
in_port = "0001"
print( int(in_port) )
"""

"""
from pysnmp.entity.rfc3413.oneliner import cmdgen

cmdGen = cmdgen.CommandGenerator()

errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.UsmUserData('userTest', 'defaultPassword', 'defaultEncryption',
                       authProtocol=cmdgen.usmHMACMD5AuthProtocol,
                       privProtocol=cmdgen.usmDESPrivProtocol),
    cmdgen.UdpTransportTarget(('192.168.90.102', 161)),
    "1.3.6"

)

if errorIndication:
    print(errorIndication)
else:
    if errorStatus:
        print('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
            )
        )
    else:
        for varBindTableRow in varBindTable:
            for name, val in varBindTableRow:
                print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
"""
"""
test = "ffffffffffff"

test = int( test , 16 )
print(test)


for i,j in enumerate(range(5,10)):
    print( str(i) + " " + str(j) )\
"""
"""
import socket
import sys

s =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(4)
s.connect(('192.168.90.101', 6633))

try :
    data = s.recv(4096)
    data = s.recv(4096)
    print( data )
except Exception as err:
    print( "Handling run-time error : " + err )
"""


