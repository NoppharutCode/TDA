"""
Created on Mon Jan 02 20:18:09 2017

@author: Noppharut
"""
import socket
import struct
import binascii
import sys
import threading
from rwlock import RWLock

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

from pyof.v0x01.asynchronous.port_status import PortStatus as portStatus
from pyof.v0x01.asynchronous.port_status import PortReason as portReason

from pyof.v0x01.symmetric.echo_reply import EchoReply as echoReply
from pyof.v0x01.symmetric.echo_request import EchoRequest as echoRequest

from lldp import lldp

from pysnmp.entity.rfc3413.oneliner import cmdgen


class Switch(threading.Thread):
    
    def __init__( self , controllerIp , controllerPort , buffer_size , switchIp , dictAllActivePortInTDA , lock ,communityString="public"):



        threading.Thread.__init__(self)
        # set init value
        self.controllerIp = controllerIp
        self.controllerPort = int(controllerPort)
        self.buffer_size = int(buffer_size)
        self.switchIp = switchIp
        self.dictActivePort = {}
        self.dictRemoteSwitchDataFromPort = {}
        self.dictAllActivePortInTDA = dictAllActivePortInTDA
        self.datapathId = None

        self.lock = lock

        self.numberOfRetransmission = 3

        # for snmpv2
        self.communityString = communityString

        #show ip of switch
        print( "Switch IP : " + self.switchIp + " Start!!!!" )

        """
        #show ip and port of controlller
        print("controller ip : " + str(self.controllerIp))
        print("controller port : " + str(self.controllerPort)) 
        """

    def createLLDPPacket(self, srcEthernet, chassis_id, port_id ):

        # create LLDP frame
        lldp_data = lldpMsg()
        lldp_data.chassis_id = tlvLLDP(1, 7,binaryData(chassis_id))
        lldp_data.port_id = tlvLLDP(2, 2, binaryData(port_id))
        lldp_data = lldp_data.pack()

        # create etherner frame
        ethernet_data = ethernet()
        ethernet_data.destination = "01:80:c2:00:00:0e"
        ethernet_data.source = srcEthernet
        ethernet_data.type = 35020
        ethernet_data.data = lldp_data
        return ethernet_data.pack()
        #ethernet_data = ethernet_data.pack()

        """
        # create OF_PACKET_IN message
        packed_data = pI()
        packed_data.header.xid = 0
        packed_data.buffer_id = 4294967295
        packed_data.in_port = in_port
        packed_data.reason = pIR.OFPR_ACTION
        packed_data.data = ethernet_data
        packed_data.total_len = packed_data.get_size()-8
        packed_data = packed_data.pack()
        return packed_data
        """

    def getPortFromSnmpVersion2C(self, mininetOption, initConnection):
        # init value
        count = 0
        cmdGen = None
        tempHwAddr = ""
        # list port
        dictPort = {}
       
        try : 
            # create object for create snmp command
            cmdGen = cmdgen.CommandGenerator()
        except Exception as err :
            print( " 94 Switch ip " + self.switchIp + " terminate because handling run-time error : " + str( err ) )
            sys.exit()

        while count < self.numberOfRetransmission :
            try :
                # connect to snmp at switch
                errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
                    cmdgen.CommunityData('public'),
                    cmdgen.UdpTransportTarget( ( self.switchIp , 161 ) ),
                    '1.0.8802.1.1.2.1.3.7.1.3',
                    '1.0.8802.1.1.2.1.3.7.1.4'
                )

                if errorIndication:
                    print(errorIndication)
                    count += 1
                else:
                    if errorStatus:
                        print('%s at %s' % (
                            errorStatus.prettyPrint(),
                            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                            )
                        )
                        count += 1
                    else:
                        # init value
                        #index = 1
                        
                        # number of port
                        if mininetOption == 1 and len( varBindTable ) > 0 :
                            del varBindTable[ len(varBindTable) - 1 ]


                        for i in varBindTable :
                                
                            # mac address
                            tempHwAddr = i[0][1].prettyPrint()
                            tempHwAddr = tempHwAddr[2:len(tempHwAddr)]

                            if ( len(tempHwAddr) != 12 ) :
                                print("Error invalid mac address from local port in snmp")
                            else:
                                    
                                    
                                tempHwAddr = tempHwAddr[0:2] + ":" + tempHwAddr[2:4] + ":" + tempHwAddr[4:6] + ":" + tempHwAddr[6:8] + ":" + tempHwAddr[8:10] + ":" + tempHwAddr[10:12]
                                tempPPort = PPort(i[0][0][-1], tempHwAddr , i[1][1].prettyPrint(), 0, 0, 192 ,0,0,0)

                                dictPort[ str(i[0][0][-1]) ] = tempPPort  # type interger chage to str

                                """
                                print("key : " + str(i[0][0][-1]) )
                                print("item  : " + tempPPort )
                                    
                                """

                                """
                                    key : poistion of active port in snmp (2)
                                    item : PPort(object)
                                """
                                
                            #index += 1
                            
                        return dictPort , tempHwAddr


                
            except Exception as err :
                count += 1
                print( " 165 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )

        
        print( " Switch ip " + self.switchIp + " terminate because : it has problem about snmp ")
        if initConnection:
            sys.exit()
        else:
            return dictPort , None
    
    def getRemoteSwitchDataFromSnmpVersion2C(self, initConnection):

        # init value
        count = 0
        cmdGen = None
        dictRemoteSwitchDataFromPort = {}

        try : 
            # create object for create snmp command
            cmdGen = cmdgen.CommandGenerator()
        except Exception as err :
            print( " Switch ip " + self.switchIp + " 226 terminate because handling run-time error : " + str( err ) )
            sys.exit()

        while count < self.numberOfRetransmission :
            try :
                # <snmpv2c>
                errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
                    cmdgen.CommunityData('public'),
                    cmdgen.UdpTransportTarget((self.switchIp, 161)),
                    '1.0.8802.1.1.2.1.4.1.1.5',
                    '1.0.8802.1.1.2.1.4.1.1.7',
                    '1.0.8802.1.1.2.1.4.1.1.8',
                    '1.0.8802.1.1.2.1.4.1.1.4',
                    '1.0.8802.1.1.2.1.4.1.1.6'
                )

                if errorIndication:
                    print(errorIndication)
                    count += 1
                else:
                    if errorStatus:
                        print('%s at %s' % (
                            errorStatus.prettyPrint(),
                            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                            )
                        )
                        count += 1
                    else:

                        #init value
                        tempPortID = ""
                        chassisIdSubType = ""
                        portIdSubType = ""
                        firstData = None
                        secondData = None
                        status = None
                   
                        for i in varBindTable:

                            chassisIdSubType = i[3][1].prettyPrint()
                            portIdSubType = i[4][1].prettyPrint()

                            if chassisIdSubType == "7" and portIdSubType == "2":
                                firstData = i[0][1].prettyPrint()
                                tempPortID = i[1][1].prettyPrint()[2:] # 00000001
                                # change 00000001 to \x00\x00\x00\x01
                                packer = struct.Struct('bbbb')
                                secondData = packer.pack( int( tempPortID[0:2] , 16 ) , int( tempPortID[2:4] , 16 ) , int( tempPortID[4:6] , 16 ) , int( tempPortID[6:8] , 16 ))
                                status = True                            
                            elif chassisIdSubType == "4" and portIdSubType == "3" :
                                firstData = i[0][1].prettyPrint()
                                secondData = i[2][1].prettyPrint()
                                status = False
                            """ 
                                key = poistion of active port at recvice remote data in snmp (int : 2)
                                index 0 = datapath id (str : dpid:0000000000000001)
                                index 1 = port no (binary : b'\x00\x00\x00\x01')
                                index 2 = check status (datapath_id, port_no) or (hw_addr, hw_desc)
                            """
                            dictRemoteSwitchDataFromPort[str(i[0][0][-2])] = [ firstData , secondData , status ]
                            """printedit"""
                            """
                            print("dictRemoteSwitchDataFromPort : ")
                            print( "key : " + str(i[0][0][-2]) )
                            print( "index 0 : " + dictRemoteSwitchDataFromPort[str(i[0][0][-2])][0] )
                            print( "index 1 : " + str(dictRemoteSwitchDataFromPort[str(i[0][0][-2])][1]) )
                            print( "index 2 : " + str(dictRemoteSwitchDataFromPort[str(i[0][0][-2])][2]) )
                            """

                        
                        #print("remote port list : ")
                        #print(dictRemoteSwitchDataFromPort)
                        return dictRemoteSwitchDataFromPort
                # </snmpv2c>
            except Exception as err :
                print( " 277 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )
                count += 1
        print( " Switch ip " + self.switchIp + " terminate because : it has problem about snmp ")
        if initConnection:
            sys.exit()
        else:
            return dictRemoteSwitchDataFromPort

    def receiveDataFromSocket(self):
        
        data = None
        count = 0
        while count < self.numberOfRetransmission :
            try :
                data = self.s.recv(self.buffer_size)
                return data
            except Exception as err:
                count += 1
                print( " 291 Switch ip " + self.switchIp + " handling run-time error of socket : " + str( err ) )
        
        print( " Switch ip " + self.switchIp + " terminate" )
        sys.exit()
        
    

    def sendAndReceiveOF_HELLO_OPENFLOWV1(self):

        #init value
        count = 0
        tempBytes = None

        # create OF_HEllO message
        packed_data = Hello().pack()

        while count < self.numberOfRetransmission :
            try:

                # send OF_HEllO message to contoller
                self.s.send(packed_data)
                print( "Switch ip " + self.switchIp + " Send OF_HELLO message to controller")

                # receive OF_HELLO message from controller
                data = self.s.recv(self.buffer_size)
                #print("hello message len : " + str(len(data)) )

                # temp for byte data
                tempBytes = data

                data = unpack_message(data)

                if data.header.message_type.name == "OFPT_HELLO" :
                    print( "Switch ip " + self.switchIp + " Receive OF_HELLO message from controller") 
                    if len(tempBytes) == 8:
                        return False , None
                    else:
                        #print(tempBytes[8:16])
                        return True , tempBytes[8:16]

            except Exception as err : 
                count += 1
                print( " 322 Switch ip " + self.switchIp + " handling run-time error of socket : " + str(err) )
            
            print( " Switch ip " + self.switchIp + " terminate" )
            sys.exit()

    def sendAndReceiveOF_FEATURE_OPENFLOWV1(self, checkData, tempBytes ):

        try : 
            # receive OF_FEATURE_REQUEST message
            if checkData:
                data = tempBytes
            else:
                data = self.receiveDataFromSocket()
            
            print( "Switch ip " + self.switchIp + " Receive OF_FEATURE_REQUEST message from controller")
            data = unpack_message(data)

            if  data.header.message_type.name != "OFPT_FEATURES_REQUEST" :
                print( " 336 Switch ip " + self.switchIp + " terminate because switch don't receive OF_FEATURES_REQUEST" )
                sys.exit()

            # get tranID from OF_FEATURE_REQUEST message
            tranID = data.header.xid

            #send OF_FEATURE_REPLY message

            listPort = []

            dictPort , tempHwAddr = self.getPortFromSnmpVersion2C( 0 , True )
            dictRemoteSwitchData = self.getRemoteSwitchDataFromSnmpVersion2C( True )
            
                       
        
            for snmpPosition in dictPort :
                if snmpPosition in dictRemoteSwitchData :
                    self.dictActivePort[snmpPosition] = dictPort[snmpPosition]
                    listPort.append(dictPort[snmpPosition])
            
            
            print("list active port " + self.switchIp +  " : ")
            for key, port in self.dictActivePort.items() :
                print("snmp position : " + key + " | hw_addr : " + str(port.hw_addr) + " | port_no : " + str(port.port_no) )
                      
            # find max value of mac address from list mac address
            maxPort = "000000000000"
            maxIndex = 0
            
            for index , item in enumerate( listPort ):
                tempMac = item.hw_addr.replace(":","")
                if ( int( tempMac , 16 ) > int( maxPort , 16 ) ):
                    maxPort = tempMac
                    maxIndex = index

            # create OF_FEATURE_REPLY message
            packed_data = FeaRes()
            packed_data.header.xid = tranID


            # gen datapath_id from hw_addr of first port
            tempDataPathId = None
            if len(listPort) > 0 :
                tempDataPathId = listPort[maxIndex].hw_addr + ":ff:ff"
            else:
                tempDataPathId = tempHwAddr + ":ff:ff"

            packed_data.datapath_id = tempDataPathId
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

            # send OF_FEATURE_REPLY message
            self.s.send(packed_data)
            print("Send OF_FEATURE_REPLY message to controller")

            #record datapath id 
            self.datapathId = tempDataPathId
            self.datapathId = "dpid:"+ self.datapathId.replace(":","")

            """
            tempPortID = i[1][1].prettyPrint()[2:] # 00000001
            # change 00000001 to \x00\x00\x00\x01
            packer = struct.Struct('bbbb')
            secondData = packer.pack( int( tempPortID[0:2] , 16 ) , int( tempPortID[2:4] , 16 ) , int( tempPortID[4:6] , 16 ) , int( tempPortID[6:8] , 16 ))
            """

            try :
                if len(self.dictActivePort) > 0 :
                    self.lock.acquire_write()
                    # add port to dict all active port in tda
                    for snmpPosition, port in self.dictActivePort.items():
                        tempPortID = str(port.port_no)
                        tempPortID = ("0" * ( 8 - len(tempPortID)) ) + tempPortID
                        packer = struct.Struct('bbbb')
                        tempPortID = packer.pack( int( tempPortID[0:2] , 16 ) , int( tempPortID[2:4] , 16 ) , int( tempPortID[4:6] , 16 ) , int( tempPortID[6:8] , 16 ))
                        self.dictAllActivePortInTDA[ ( port.hw_addr, port.name ) ] = [self.datapathId , tempPortID]
                    self.lock.release()

                print(self.dictAllActivePortInTDA)
            except Exception as err :
                self.lock.release()
                print( " 422 Switch ip " + self.switchIp + " terminate because handling run-time error : " + str( err ) )
                sys.exit()

        except Exception as err :
            print( " 426 Switch ip " + self.switchIp + " terminate because handling run-time error : " + str( err ) )
            sys.exit()

    def checkStatusOfActivePort(self):

       
        tempDictActivePort = {}
        # dict for activeport at cal ma
        listDictPortPresent = {}
        

        dictPort , tempHwAddr = self.getPortFromSnmpVersion2C( 0 , False )
        if tempHwAddr != None:
            dictRemoteSwitchData = self.getRemoteSwitchDataFromSnmpVersion2C( False )
        else:
            dictRemoteSwitchData = {}
        
        
        if self.switchIp == "192.168.0.104":
            print("--------------192.168.0.104-----------------")
            print("active port before check :  self.dictActivePort")
            print(self.dictActivePort)
            print("active port before check :  self.dictAllActivePortInTDA")
            print(self.dictAllActivePortInTDA)
            print("--------------192.168.0.104-----------------")
        

        for snmpPosition in dictPort :
            if snmpPosition in dictRemoteSwitchData :
                listDictPortPresent[snmpPosition] = dictPort[snmpPosition]
         
        for snmpPosition , port in listDictPortPresent.items():
            #print("55555555 : " + port.hw_addr)
            if snmpPosition in self.dictActivePort:
                tempDictActivePort[snmpPosition] = port
                del self.dictActivePort[snmpPosition]
            else:
                #send new port to controller

                tempDictActivePort[snmpPosition] = port
                packed_data = portStatus( reason=portReason.OFPPR_ADD , desc=port )
                packed_data = packed_data.pack()
                self.s.send( packed_data )
                
                try:
                    tempPortID = str(port.port_no)
                    tempPortID = ("0" * ( 8 - len(tempPortID)) ) + tempPortID
                    packer = struct.Struct('bbbb')
                    tempPortID = packer.pack( int( tempPortID[0:2] , 16 ) , int( tempPortID[2:4] , 16 ) , int( tempPortID[4:6] , 16 ) , int( tempPortID[6:8] , 16 ))
                    self.lock.acquire_write()
                    # add port to dict all active port in tda
                    self.dictAllActivePortInTDA[ ( port.hw_addr , port.name ) ] = [ self.datapathId , tempPortID ]
                    self.lock.release()
                except:
                    self.lock.release()
                #print("release at add port")
                           
        #send del port to controller
        for snmpPosition , port in self.dictActivePort.items():
            packed_data = portStatus( reason=portReason.OFPPR_DELETE , desc=port )
            packed_data = packed_data.pack()
            self.s.send( packed_data )
        
        # del port from dict all active port in TDA
        if len(self.dictActivePort.items()) > 0 :
            self.lock.acquire_write()
            for snmpPosition , port in self.dictActivePort.items():
                """
                print("--------------delete-------------")
                print("hw_addr : " + port.hw_addr)
                print("hw_desc : " + port.name)
                print(self.dictAllActivePortInTDA)
                """
                del self.dictAllActivePortInTDA[ ( port.hw_addr , port.name ) ]
                """
                print(self.dictAllActivePortInTDA)
                print("--------------delete-------------")
                """
            self.lock.release()

        
        if self.switchIp == "192.168.0.104":
            print("--------------192.168.0.104-----------------")
            print("active port after check :  tempDictActivePort")
            print(tempDictActivePort)
            print("active port after check :  self.dictAllActivePortInTDA")
            print(self.dictAllActivePortInTDA)
            print("--------------192.168.0.104-----------------")
        
        del self.dictActivePort
        self.dictActivePort = tempDictActivePort   
        #print("Active Port : " + self.switchIp) 
        #print(tempDictActivePort)
        del self.dictRemoteSwitchDataFromPort
        self.dictRemoteSwitchDataFromPort = dictRemoteSwitchData
        
        
    def searchSnmpPosition(self, portNumber):
        for key , port in self.dictActivePort.items() :
            if port.port_no == portNumber :
                return key , port
                #print("key : " + key + " port : " + str(port) + " hw_addr : " + str(port.hw_addr) +" port_no : " + str(port.port_no))
        return None, None

    def sendLLDPInOF_PACKET_IN_OPENFLOWV1( self, data ):

        try :
            # ethernet header of lldp
            ethernetH = data.data.value
            ethernetH = lldp.unpack_ethernet_frame(ethernetH)

            # check paket is lldp
            if ethernetH[3] != 35020 :
                return True

            # get Src from ethernet header
            temp = ethernetH[2] # tuple
            temp = list(map(str, temp)) # tuple to list

            srcEthernet = ""
            hexNumberTemp = ""
            for i in temp:
                hexNumberTemp = hex(int(i))[2:] # change number to Hex cut 0x out
                if(len(hexNumberTemp) == 1):
                    srcEthernet  += "0" + hexNumberTemp
                else:
                    srcEthernet += hexNumberTemp
                srcEthernet += ":"

            srcEthernet = srcEthernet[0: len(srcEthernet)-1] # src ethernet
           
            
            #data.actions[0].port is output_field
            #print("output port : " + str(data.actions[0].port))
            snmpPosition, tempPort = self.searchSnmpPosition(data.actions[0].port)
            
            """
            for key , port in self.listActivePort.items():
                print("snmp poisition : " + key + " port : " + port.hw_addr)
            """
            """
            if snmpPosition == "5" :
                print("snmpposition : " + snmpPosition + " port : " + str(tempPort.hw_addr))
            """

            # init value
            chassis_id = None
            port_id = None

            # self.dictRemoteSwitchDataFromPort[snmpPosition][2] may be = None
            if self.dictRemoteSwitchDataFromPort[snmpPosition][2] :
                # send Packet_IN contain lldp frame
                chassis_id = self.dictRemoteSwitchDataFromPort[snmpPosition][0]
                port_id = self.dictRemoteSwitchDataFromPort[snmpPosition][1]
                in_port = tempPort.port_no
                
                #print("port : " + str(port_id))
            else :

                tempHwAddr = self.dictRemoteSwitchDataFromPort[snmpPosition][0][2:]
                tempHwAddr = tempHwAddr[0:2] + ":" + tempHwAddr[2:4] + ":" + tempHwAddr[4:6] + ":" + tempHwAddr[6:8] + ":" + tempHwAddr[8:10] + ":" + tempHwAddr[10:12]

                try:
                    self.lock.acquire_read()
                    chassis_id = self.dictAllActivePortInTDA[(tempHwAddr, self.dictRemoteSwitchDataFromPort[snmpPosition][1])][0] 
                    port_id = self.dictAllActivePortInTDA[(tempHwAddr, self.dictRemoteSwitchDataFromPort[snmpPosition][1])][1] 
                    self.lock.release()
                except Exception as err : 
                    self.lock.release()
                in_port = tempPort.port_no
        
            if chassis_id == None:
                return False
            ethernet_data = self.createLLDPPacket( srcEthernet  , bytes(chassis_id, encoding='utf-8') , port_id )

            """
            if self.switchIp == "192.168.0.104":
                print("port_no type : " + str(type(port_id)))
                print("port_no : " + str(port_id))
            """

            # create OF_PACKET_IN message
            packed_data = pI()
            packed_data.header.xid = 0
            packed_data.buffer_id = 4294967295
            packed_data.in_port = in_port
            packed_data.reason = pIR.OFPR_ACTION
            packed_data.data = ethernet_data
            packed_data.total_len = packed_data.get_size()-8
            packed_data = packed_data.pack()

            # OF_PACKET_IN -> controller
            self.s.send( packed_data )
            #print("switch ip " + self.switchIp + " send OFPT_PACKET_IN")
            return True

        except Exception as err:

            print( " 514 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )
            return False


    def packetHandler(self):
        pass

    def openflowV1(self):

        # init value
        data = None
        checkData = None
        tempBytes = None

        # OF_HELLO switch <-> controller
        checkData , tempBytes = self.sendAndReceiveOF_HELLO_OPENFLOWV1()
    
        # OF_FEATURE switch <-> controller
        self.sendAndReceiveOF_FEATURE_OPENFLOWV1(checkData, tempBytes)
        
        """
        port = PPort(100, "ff:ff:ff:ff:ff:00" , "test", 0, 0, 192 ,0,0,0)
        port.port_no = 200
        print( "add port : " + str(port.port_no))
        packed_data = portStatus( reason=portReason.OFPPR_ADD , desc=port )
        packed_data = packed_data.pack()
        self.s.send( packed_data )  
        """
        count = 0
        while(1):

            #init value 
            indexData = 0 
            tempData = None
            try:
                tempData = self.s.recv(self.buffer_size)
            except Exception as err:
                count += 1
            

            if tempData != None :

                self.checkStatusOfActivePort()

                while indexData < len(tempData):
                
                    data = unpack_message(tempData[indexData:])
                    if data.header.message_type.name == "OFPT_PACKET_OUT":
                        
                        # OF_PACKET_IN -> controller
                        check = self.sendLLDPInOF_PACKET_IN_OPENFLOWV1( data )

                        if check:
                            count = 0
                        else:
                            count = 2
                        """
                        if not check :
                            print("switch ip " + self.switchIp + " send OFPT_ECHO_REQUEST")
                            packet = echoRequest().pack()
                            self.s.send(packet)
                        """

                    indexData += data.header.length
            
            if count == 2:
                count = 0
                #print("switch ip " + self.switchIp + " send OFPT_ECHO_REQUEST")
                packet = echoRequest().pack()
                self.s.send(packet)

            """
            if data.header.message_type.name == "OFPT_ECHO_REQUEST":
                print("Send OFPT_ECHO_REPLY")
                packet = echoReply().pack()
                self.s.send(packet)
            """


            """
            if data.header.message_type.name == "OFPT_ECHO_REPLY":
                print("send OFPT_ECHO_REQUEST")
                packet = echoRequest().pack()
                self.s.send(packet)    
            """
              
        
    def startConnectToController(self):

        # create socket and connection to controller
        self.s =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setimeout
        self.s.settimeout(5)
        self.s.connect((self.controllerIp, self.controllerPort))

        print("Switch ip " + self.switchIp + " create socket success!!!")

        self.openflowV1()

    def stopConnectToController(self):
        self.s.close()

    def run(self):
        try:
            self.startConnectToController()
        finally:
            self.stopConnectToController()

if __name__ == '__main__':
    dictAllActivePortInTDA = {}
    tda = Switch('192.168.0.101', 6633, 8192, '192.168.0.104', dictAllActivePortInTDA , RWLock())
    #tda.createOFFeatureReplyFromSnmp(111,1)
    tda.startConnectToController()
    num = input()   
    tda.stopConnectToController()



    
