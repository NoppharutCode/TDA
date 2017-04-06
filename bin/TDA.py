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
from pyof.v0x01.common.utils import unpack_message as uM
from pyof.foundation.network_types import Ethernet as ethernet
from pyof.foundation.network_types import LLDP as lldpMsg
from pyof.foundation.network_types import TLVWithSubType as tlvLLDP
from pyof.foundation.basic_types import DPID as dpid
from pyof.foundation.basic_types import BinaryData as binaryData
from lldp import lldp

class TDA(object):

    def __init__(self,ip,port,buffer_size):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        print("controller ip : " + str(self.ip))
        print("controller port : " + str(self.port)) 

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

        # create OF_FEATURE_REPLY message
        packed_data = FeaRes()
        packed_data.header.xid = tranID
        packed_data.datapath_id = '00:00:00:00:00:00:00:01'
        packed_data.n_buffers = 256
        packed_data.n_tables = 254
        packed_data.capabilities = 199
        packed_data.actions = 4095
        # create port
        port1 = PPort(1, '00:00:00:00:00:01','eth1', 0, 0, 192 ,0,0,0)
        packed_data.ports = [port1]
        packed_data = packed_data.pack()

        self.s.send(packed_data)
        
        # receive OF_FLOW_MOD message
        data = self.s.recv(self.buffer_size)
        data = uM(data)
        print(data)

        # receive OF_PACKET_OUT message
        data = self.s.recv(self.buffer_size)
        data = uM(data)

        # Ethernet Header of lldp
        ethernetH = data.data.value
        ethernetH = lldp.unpack_ethernet_frame(ethernetH)

        # Ethernet payload of lldp
        ethernetP = ethernetH[4]
        ethernetP = lldp.unpack_lldp_frame(ethernetP)

       
        """
        num = input()
        #b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x33'
        # create LLDP message
        lldp_data = lldpMsg()
        lldp_data.chassis_id = tlvLLDP(1, 7,binaryData(b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x31'))
        lldp_data.port_id = tlvLLDP(2, 2, binaryData(b'\x00\x00\x00\x01'))
        lldp_data = lldp_data.pack()
        # create EthernerFrame message
        ethernet_data = ethernet()
        ethernet_data.destination = "01:80:c2:00:00:0e"
        ethernet_data.source = "00:00:00:00:00:02"
        ethernet_data.type = 35020
        ethernet_data.data = lldp_data
        ethernet_data = ethernet_data.pack()
        # create OF_PACKET_IN message
        packed_data = pI()
        packed_data.header.xid = 0
        packed_data.buffer_id = 4294967295
        packed_data.total_len = 60
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
    tda = TDA('192.168.90.101', 6633, 4096)
    tda.startConnectToController()
    num = input()   
    tda.stopConnectToController()
