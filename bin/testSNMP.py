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
        """
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