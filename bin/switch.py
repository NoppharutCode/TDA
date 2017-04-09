"""
Created on Mon Jan 02 20:18:09 2017

@author: Noppharut
"""

import socket
import struct
import binascii
import sys

from pyof.v0x01.controller2switch.features_request import FeaturesRequest as FeaReq
from pyof.v0x01.controller2switch.features_reply import FeaturesReply as FeaRes
from pyof.v0x01.symmetric.hello import Hello as Hello
from pyof.v0x01.common.phy_port import PhyPort as PPort
from pyof.v0x01.asynchronous.packet_in import PacketIn as pI
from pyof.v0x01.asynchronous.packet_in import PacketInReason as pIR
from pyof.v0x01.common.utils import unpack_message
from pyof.foundation.network_types import Ethernet as ethernet
from pyof.foundation.network_types import LLDP as lldpMsg
from pyof.foundation.network_types import TLVWithSubType as tlvLLDP
from pyof.foundation.basic_types import DPID as dpid
from pyof.foundation.basic_types import BinaryData as binaryData

from lldp import lldp

from pysnmp.entity.rfc3413.oneliner import cmdgen

class Switch(object):

    def __init__(self,ip,port,buffer_size):

        # set init value
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size

        #show ip and port of controlller
        print("controller ip : " + str(self.ip))
        print("controller port : " + str(self.port)) 

    def createLLDPPacket(self, srcEthernet, chassis_id, port_id):

        # create LLDP frame
        lldp_data = lldpMsg()
        lldp_data.chassis_id = tlvLLDP(1, 7,binaryData(b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x31'))
        lldp_data.port_id = tlvLLDP(2, 2, binaryData(b'\x00\x00\x00\x01'))
        lldp_data = lldp_data.pack()

        # create etherner frame
        ethernet_data = ethernet()
        ethernet_data.destination = "01:80:c2:00:00:0e"
        ethernet_data.source = srcEthernet
        ethernet_data.type = 35020
        ethernet_data.data = lldp_data
        ethernet_data = ethernet_data.pack()

        # create OF_PACKET_IN message
        packed_data = pI()
        packed_data.header.xid = 0
        packed_data.buffer_id = 4294967295
        packed_data.in_port = 1
        packed_data.reason = pIR.OFPR_ACTION
        packed_data.data = ethernet_data
        packed_data.total_len = packed_data.get_size()-8
        packed_data = packed_data.pack()
        return packed_data

    def firstConnectToSnmp(self, tranID):

        # list port
        listPort = []
       
        # create object for create snmp command
        cmdGen = cmdgen.CommandGenerator()

        # connect to snmp at switch
        errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
            cmdgen.CommunityData('public'),
            cmdgen.UdpTransportTarget(('192.168.90.110', 161)),
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
                # init value
                index = 0
                name, val = "" , ""

                # number of port
                size = (int)(len(varBindTable)/3)

                # check number of port should > 0
                if(size > 0):
                    while(index < size):
                        tempHwAddr = varBindTable[index+size][0][1].prettyPrint()
                        tempHwAddr = tempHwAddr[2:len(tempHwAddr)]
                        if ( len(tempHwAddr) != 12 ) :
                            print("Error")
                        else:
                            tempHwAddr = tempHwAddr[0:2] + ":" + tempHwAddr[2:4] + ":" + tempHwAddr[4:6] + ":" + tempHwAddr[6:8] + ":" + tempHwAddr[8:10] + ":" + tempHwAddr[10:12]

                        listPort.append(PPort(index + 1, tempHwAddr , varBindTable[ index+( size*2 ) ][0][1].prettyPrint(), 0, 0, 192 ,0,0,0))
                        index += 1
                else:
                    print("Error : switch doesn't have active port")
            

            for i in listPort:
                print("Hw_addr : " + i.hw_addr)
                print("Hw_desc : " + i.name)

        
        # create OF_FEATURE_REPLY message
        packed_data = FeaRes()
        packed_data.header.xid = tranID

        # gen datapath_id from hw_addr of first port
        packed_data.datapath_id = listPort[0].hw_addr + ":ff:ff"
        #packed_data.datapath_id = '00:00:00:00:00:00:00:02'

        packed_data.n_buffers = 256
        packed_data.n_tables = 254
        packed_data.capabilities = 199
        packed_data.actions = 4095

        # create port
        #port1 = PPort(1, '00:00:00:00:00:02','eth1', 0, 0, 192 ,0,0,0)
        #packed_data.ports = [port1]
        packed_data.ports = listPort
        packed_data = packed_data.pack()

        return packed_data
        
    
    def startConnectToController(self):

        # create socket and connection to controller
        self.s =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ip, self.port))
        print("create socket success!!!")

        # create OF_HEllO message
        packed_data = Hello().pack()

        # send OF_HEllO message to contoller
        self.s.send(packed_data)

        # receive OF_HELLO message
        data = self.s.recv(self.buffer_size)

        # receive OF_FEATURE_REQUEST message
        data = self.s.recv(self.buffer_size)

        # get tranID from OF_FEATURE_REQUEST message
        packer = struct.Struct('HHI')
        packed_decode = packer.unpack(data)
        tranID = packed_decode[2]

        packed_data = self.firstConnectToSnmp(tranID)

        #send OF_FEATURE_REPLY message
        self.s.send(packed_data)


        # tum tong ni yu
        
        # receive OF_FLOW_MOD message
        data = self.s.recv(self.buffer_size)
        data = unpack_message(data)
        print(data)

        # receive OF_PACKET_OUT message
        data = self.s.recv(self.buffer_size)
        data = unpack_message(data)

        # ethernet header of lldp
        ethernetH = data.data.value
        ethernetH = lldp.unpack_ethernet_frame(ethernetH)
        # get Src from ethernet header
        temp = ethernetH[2] # tuple
        temp = list(map(str, temp)) # tuple to list
        srcEthernet = ""
        for i in temp:
            if(len(i)== 1):
                srcEthernet += "0"
            srcEthernet += i +":"
        srcEthernet = srcEthernet[0: len(srcEthernet)-1] # src ethernet
        # ethernet payload of lldp
        ethernetP = ethernetH[4]
        ethernetP = lldp.unpack_lldp_frame(ethernetP)
        list_TLV = []
        for i in ethernetP:
            list_TLV.append(i)

        """
        self.s.send(self.createLLDPPacket( srcEthernet, list_TLV[0], list_TLV[1]))

        while(1):
            data = self.s.recv(self.buffer_size)
            self.s.send(self.createLLDPPacket( srcEthernet, list_TLV[0], list_TLV[1]))

        """
        """
        #b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x33'
        # create LLDP message
        lldp_data = lldpMsg()
        lldp_data.chassis_id = tlvLLDP(1, 7,binaryData(b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x31'))
        lldp_data.port_id = tlvLLDP(2, 2, binaryData(b'\x00\x00\x00\x01'))
        lldp_data = lldp_data.pack()
        # create EthernerFrame message
        ethernet_data = ethernet()
        ethernet_data.destination = "01:80:c2:00:00:0e"
        ethernet_data.source = "00:00:00:00:00:01"
        ethernet_data.type = 35020
        ethernet_data.data = lldp_data
        ethernet_data = ethernet_data.pack()
        # create OF_PACKET_IN message
        packed_data = pI()
        packed_data.header.xid = 0
        packed_data.buffer_id = 4294967295
        packed_data.in_port = 1
        packed_data.reason = pIR.OFPR_ACTION
        packed_data.data = ethernet_data
        packed_data.total_len = packed_data.get_size()-8
        packed_data = packed_data.pack()
        self.s.send(packed_data)
        print('susu')

        """

        

        """
        print(data.data)
        print(dir(lldp))
        print(dir(data.data))
        print(lldp.unpack_ethernet_frame(data.data.value))
        """
        """
        packer = struct.Struct('BBHL')
        packed_decode = packer.unpack_from(data)
        print(packed_decode)
        """
        

    def stopConnectToController(self):
        self.s.close()

if __name__ == '__main__':
    tda = Switch('192.168.90.101', 6633, 4096)
    tda.firstConnectToSnmp(111)
    #tda.startConnectToController()
    #num = input()   
    #tda.stopConnectToController()
    