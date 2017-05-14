"""
Created on Mon Jan 02 20:18:09 2017

@author: Noppharut
"""

import socket
import struct
import binascii
import sys
import threading

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

    def __init__( self , controllerIp , controllerPort , buffer_size , switchIp , communityString="public"):



        threading.Thread.__init__(self)
        # set init value
        self.controllerIp = controllerIp
        self.controllerPort = int(controllerPort)
        self.buffer_size = int(buffer_size)
        self.switchIp = switchIp
        self.listActivePort = {}
        self.listRemoteDataFromPort = {}


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

    def getActivePortFromSnmpVersion2C(self, mininetOption):

        # init value
        count = 0
        cmdGen = None

        # list port
        listPort = []
       
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
                        index = 1
                        
                        # number of port
                        if mininetOption == 1 and len( varBindTable ) > 0 :
                            del varBindTable[ len(varBindTable) - 1 ]

                        # check number of port should > 0
                        if( len(varBindTable) > 0 ):


                            for i in varBindTable :
                                
                                # mac address
                                tempHwAddr = i[0][1].prettyPrint()
                                tempHwAddr = tempHwAddr[2:len(tempHwAddr)]

                                if ( len(tempHwAddr) != 12 ) :
                                    print("Error invalid mac address from local port in snmp")
                                else:
                                    
                                    
                                    tempHwAddr = tempHwAddr[0:2] + ":" + tempHwAddr[2:4] + ":" + tempHwAddr[4:6] + ":" + tempHwAddr[6:8] + ":" + tempHwAddr[8:10] + ":" + tempHwAddr[10:12]
                                    tempPPort = PPort(i[0][0][-1], tempHwAddr , i[1][1].prettyPrint(), 0, 0, 192 ,0,0,0)

                                    self.listActivePort[ str(i[0][0][-1]) ] = tempPPort  # type interger chage to str

                                    """
                                    print("key : " + str(i[0][0][-1]) )
                                    print("item  : " + tempPPort )
                                    
                                    """

                                    """
                                        key : poistion of active port in snmp (2)
                                        item : PPort(object)
                                    """
                                listPort.append( tempPPort )
                                index += 1
                            

                            return listPort

                        else:
                            print( " 159 Switch ip " + self.switchIp + " terminate because : switch doesn't have active port please snmp")
                            sys.exit()

                
            except Exception as err :
                count += 1
                print( " 165 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )

        
        print( " Switch ip " + self.switchIp + " terminate because : it has problem about snmp ")
        sys.exit()



        """
        try :

            print("All active port of switch ip " + self.switchIp +  " : ")
            for i in listPort:
                print("Hw_addr : " + i.hw_addr)
                print("Hw_desc : " + i.name)

            

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
            packed_data.datapath_id = listPort[maxIndex].hw_addr + ":ff:ff"
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
        except Exception as err :
            print( " Switch ip " + self.switchIp + " terminate because handling run-time error : " + str( err ) )
        """
    def receiveRemoteSwitchDataFromSnmpVersion2C(self):

        # init value
        count = 0
        cmdGen = None
        self.listRemoteDataFromPort = {}

        try : 
            # create object for create snmp command
            cmdGen = cmdgen.CommandGenerator()
        except Exception as err :
            print( " Switch ip " + self.switchIp + " 226 terminate because handling run-time error : " + str( err ) )
            sys.exit()


        try :
            # <snmpv2c>
            errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
                cmdgen.CommunityData('public'),
                cmdgen.UdpTransportTarget((self.switchIp, 161)),
                '1.0.8802.1.1.2.1.4.1.1.5',
                '1.0.8802.1.1.2.1.4.1.1.7'
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

                    tempPortID = ""

                    for i in varBindTable:

                        tempPortID = i[1][1].prettyPrint()[2:] # 00000001

                        # change 00000001 to \x00\x00\x00\x01
                        packer = struct.Struct('bbbb')
                        binaryPortID = packer.pack( int( tempPortID[0:2] , 16 ) , int( tempPortID[2:4] , 16 ) , int( tempPortID[4:6] , 16 ) , int( tempPortID[6:8] , 16 ))
                            
                        """ 
                            key = poistion of active port at recvice remote data in snmp (int : 2)
                            index 0 = datapath id (str : dpid:0000000000000001)
                            index 1 = port id (binary : b'\x00\x00\x00\x01')
                        """
                        self.listRemoteDataFromPort[str(i[0][0][-2])] = [ i[0][1].prettyPrint() , binaryPortID ]

                        """
                        print( "key : " + str(i[0][0][-2]) )
                        print( "index 0 : " + i[0][1].prettyPrint() )
                        print( "index 1 : " + str(packed_encode) )
                        """
                    print("remote port list : ")
                    print(self.listRemoteDataFromPort)
                    return
            # </snmpv2c>
        except Exception as err :
            print( " 277 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )



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

        count = 0

        # create OF_HEllO message
        packed_data = Hello().pack()

        while count < self.numberOfRetransmission :
            try:

                # send OF_HEllO message to contoller
                self.s.send(packed_data)
                print( "Switch ip " + self.switchIp + " Send OF_HELLO message to controller")

                # receive OF_HELLO message from controller
                data = self.s.recv(self.buffer_size)
                data = unpack_message(data)

                if data.header.message_type.name == "OFPT_HELLO" :
                    print( "Switch ip " + self.switchIp + " Receive OF_HELLO message from controller")    
                    return

            except Exception as err : 
                count += 1
                print( " 322 Switch ip " + self.switchIp + " handling run-time error of socket : " + str(err) )
            
            print( " Switch ip " + self.switchIp + " terminate" )
            sys.exit()

    def sendAndReceiveOF_FEATURE_OPENFLOWV1(self):

        try : 
            # receive OF_FEATURE_REQUEST message
            data = self.receiveDataFromSocket()
            print( " 332 Switch ip " + self.switchIp + " Receive OF_FEATURE_REQUEST message from controller")
            data = unpack_message(data)

            if  data.header.message_type.name != "OFPT_FEATURES_REQUEST" :
                print( " 336 Switch ip " + self.switchIp + " terminate because switch don't receive OF_FEATURES_REQUEST" )
                sys.exit()

            # get tranID from OF_FEATURE_REQUEST message
            tranID = data.header.xid

            
            #send OF_FEATURE_REPLY message
            listPort = self.getActivePortFromSnmpVersion2C( 0 )


            print("All active port of switch ip " + self.switchIp +  " : ")
            for i in listPort:
                print("Hw_addr : " + i.hw_addr)
                print("Hw_desc : " + i.name)

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
            packed_data.datapath_id = listPort[maxIndex].hw_addr + ":ff:ff"
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

        except Exception as err :
            print( " 387 Switch ip " + self.switchIp + " terminate because handling run-time error : " + str( err ) )
            sys.exit()

    def initConnectionToController(self):

        count = 0

        while count < self.numberOfRetransmission :
            try:
                packed_data = Hello().pack()
                # send OF_HEllO message to contoller
                self.s.send(packed_data)
                print( "Switch ip " + self.switchIp + " Send OF_HELLO message to controller")

                # receive OF_HELLO message from controller
                data = self.s.recv(self.buffer_size)
                data = unpack_message(data)

                if data.header.message_type.name == "OFPT_HELLO" :

                    print( "Switch ip " + self.switchIp + " Receive OF_HELLO message from controller")
                    data = self.s.recv(self.buffer_size)
                    data = unpack_message(data)
                    print( " 428 Switch ip " + self.switchIp + " Receive OF_FEATURE_REQUEST message from controller")
                    if  data.header.message_type.name == "OFPT_FEATURES_REQUEST" :

                        # get tranID from OF_FEATURE_REQUEST message
                        tranID = data.header.xid

                        
                        #send OF_FEATURE_REPLY message
                        listPort = self.createOFFeatureReplyFromSnmpVersion2C( 0 )


                        print("All active port of switch ip " + self.switchIp +  " : ")
                        for i in listPort:
                            print("Hw_addr : " + i.hw_addr)
                            print("Hw_desc : " + i.name)

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
                        packed_data.datapath_id = listPort[maxIndex].hw_addr + ":ff:ff"
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
                            

                        return

            except Exception as err : 
                count += 1
                print( " 322 Switch ip " + self.switchIp + " handling run-time error of socket : " + str(err) )
            
        print( " Switch ip " + self.switchIp + " terminate" )
        sys.exit()

    def getListSnmpPositionFromSnmpVersion2C(self, mininetOption):

        # init value
        count  = 0
        cmdGen = None

        # list port
        listSnmpPosition = []
       
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
                        index = 10
                        
                        # number of port
                        if mininetOption == 1 and len( varBindTable ) > 0 :
                            del varBindTable[ len(varBindTable) - 1 ]

                        # check number of port should > 0
                        if( len(varBindTable) > 0 ):

                            for i in varBindTable :
                                
                                # mac address
                                tempHwAddr = i[0][1].prettyPrint()
                                tempHwAddr = tempHwAddr[2:len(tempHwAddr)]

                                if ( len(tempHwAddr) != 12 ) :
                                    print("Error invalid mac address from local port in snmp")
                                else:
                                    
                                    
                                    tempHwAddr = tempHwAddr[0:2] + ":" + tempHwAddr[2:4] + ":" + tempHwAddr[4:6] + ":" + tempHwAddr[6:8] + ":" + tempHwAddr[8:10] + ":" + tempHwAddr[10:12]
                                    tempPPort = PPort(i[0][0][-1], tempHwAddr , i[1][1].prettyPrint(), 0, 0, 192 ,0,0,0)
                                    

                                    listSnmpPosition.append( ( str(i[0][0][-1]), tempPPort ) )
                                    
                                    #self.listActivePort[ str(i[0][0][-1]) ] = tempPPort  # type interger chage to str

                                    """
                                    print("key : " + str(i[0][0][-1]) )
                                    print("item  : " + tempPPort )
                                    
                                    """

                                    """
                                        key : poistion of active port in snmp (2)
                                        item : PPort(object)
                                    """
                            return listSnmpPosition

                        else:
                            print( " 159 Switch ip " + self.switchIp + " terminate because : switch doesn't have active port please snmp")
                            sys.exit()

                
            except Exception as err :
                count += 1
                print( " 165 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )

        
        print( " Switch ip " + self.switchIp + " terminate because : it has problem about snmp ")
        sys.exit()     

    def checkStatusOfActivePort(self):

        listSnmpPosition = self.getListSnmpPositionFromSnmpVersion2C( 0 )
        #['2', '3', '5', '8', '9']
        tempListActivePort = {}

        # item = ( snmpPosition , PPort )
        for item in listSnmpPosition:
            print("item 1 : " + str(item[1].port_no))
            if item[0] in self.listActivePort :
                tempListActivePort[item[0]] = self.listActivePort[item[0]]
                del self.listActivePort[item[0]]
            else:
                #send new port to controller
                tempListActivePort[item[0]] = item[1]
                packed_data = portStatus( reason=portReason.OFPPR_ADD , desc=item[1] )
                packed_data = packed_data.pack()
                self.s.send( packed_data )   

        """
        num = input()
        port = self.listActivePort["06:fd:e2:ae:ab:60"][2]
        print( "delete port : " + str(port.port_no))
        packed_data = portStatus( reason=portReason.OFPPR_DELETE , desc=port )
        packed_data = packed_data.pack()
        self.s.send( packed_data )

        num = input()
        port.port_no = 10
        print( "add port : " + str(port.port_no))
        packed_data = portStatus( reason=portReason.OFPPR_ADD , desc=port )
        packed_data = packed_data.pack()
        self.s.send( packed_data )      
        
        return
        """
        
        # send del port to controller
        for snmpPosition , port in self.listActivePort.items():
            packed_data = portStatus( reason=portReason.OFPPR_DELETE , desc=port )
            packed_data = packed_data.pack()
            self.s.send( packed_data )
            

        
        #self.listActivePort 
        #print(listSnmpPosition)
        #print(tempListActivePort)
        
        print("self.listActivePort")
        for key,value in self.listActivePort.items():
            print("key : " + str(key) + " port_no : " + str(value.port_no) )
        
        print("tempListActivePort")
        for key,value in tempListActivePort.items():
            print("key : " + str(key) + " port_no : " + str(value.port_no) )
            
        del self.listActivePort
        self.listActivePort = tempListActivePort
        """
        for item in listSnmpPosition :
            print("key : " + str(item[0]) + " port_no : " + str(item[1].port_no))
        """

    def searchSnmpPosition(self, portNumber):
        for key , port in self.listActivePort.items() :
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
            #print(srcEthernet)

            #print(data.actions[0].port)

            snmpPosition, tempPort = self.searchSnmpPosition(data.actions[0].port)
            #print(dir(tempPort))
            """
            for key , port in self.listActivePort.items():
                print("snmp poisition : " + key + " port : " + port.hw_addr)
            """
            """
            if snmpPosition == "5" :
                print("snmpposition : " + snmpPosition + " port : " + str(tempPort.hw_addr))
            """

            # send Packet_IN contain lldp frame
            chassis_id = self.listRemoteDataFromPort[snmpPosition][0]
            port_id = self.listRemoteDataFromPort[snmpPosition][1]
            in_port = tempPort.port_no

            ethernet_data = self.createLLDPPacket( srcEthernet  , bytes(chassis_id, encoding='utf-8') , port_id )

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
            
            return True

        except Exception as err:
            print( " 514 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )
            return False



    def openflowV1(self):

        
        # OF_HELLO switch <-> controller
        self.sendAndReceiveOF_HELLO_OPENFLOWV1()

        # OF_FEATURE switch <-> controller
        self.sendAndReceiveOF_FEATURE_OPENFLOWV1()
        
        
        #self.initConnectionToController()
        #self.receiveRemoteSwitchDataFromSnmpVersion2C()

        # init value
        data = None

        while(1):

            count = 0
            # receive OF_PACKET_OUT message
            while count < self.numberOfRetransmission :
                try:
                    data = self.s.recv(self.buffer_size)
                    data = unpack_message(data)
                    break
                except Exception as err:
                    count += 1
                    print( " 431 Switch ip " + self.switchIp + " handling run-time error of socket : " + str( err ) )
            
            if count == self.numberOfRetransmission :
                print( " 443 Switch ip " + self.switchIp + " socket don't receive data")
                sys.exit()
        
            if data.header.message_type.name == "OFPT_PACKET_OUT":
                
                self.receiveRemoteSwitchDataFromSnmpVersion2C()
                self.checkStatusOfActivePort()
                # OF_PACKET_IN -> controller
                check = self.sendLLDPInOF_PACKET_IN_OPENFLOWV1( data )
                
                if not check :
                    print("send OFPT_ECHO_REQUEST")
                    packet = echoRequest().pack()
                    self.s.send(packet)
            
                """
          
                # ethernet header of lldp
                ethernetH = data.data.value
                ethernetH = lldp.unpack_ethernet_frame(ethernetH)
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
                #print(srcEthernet)

           
                
                # send Packet_IN contain lldp frame
                try :
                    chassis_id = self.listRemoteDataFromPort[self.listActivePort[srcEthernet][0]][0]
                    port_id = self.listRemoteDataFromPort[self.listActivePort[srcEthernet][0]][1]
                    in_port = self.listActivePort[srcEthernet][1]

                    ethernet_data = self.createLLDPPacket( srcEthernet  , bytes(chassis_id, encoding='utf-8') , port_id )

                    self.sendLLDPInOF_PACKET_IN_OPENFLOWV1( ethernet_data , in_port)
                    print( " packet_in ")
                except Exception as err:
                    print( " 514 Switch ip " + self.switchIp + " handling run-time error : " + str( err ) )
                """
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
        self.s.settimeout(4)
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

        # ethernet payload of lldp
        """
        ethernetP = ethernetH[4]
        ethernetP = lldp.unpack_lldp_frame(ethernetP)
        list_TLV = []
        for i in ethernetP:
            list_TLV.append(i)
        print(list_TLV[1])
        """
        #self.s.send(self.createLLDPPacket( srcEthernet, bytes('dpid:0000000000000001', encoding='utf-8'), list_TLV[1]))
        """
        # ethernet header of lldp
        ethernetH = data.data.value
        ethernetH = lldp.unpack_ethernet_frame(ethernetH)
        # get Src from ethernet header
        temp = ethernetH[2] # tuple
        temp = list(map(str, temp)) # tuple to list
        srcEthernet = ""
        hexNumberTemp = ""
        for i in temp:
            hexNumberTemp = hex(int(i))[2:] # change number to Hex cut 0x out
            if(len(hexNumberTemp) == 1):
                srcEthernet  += 0 + hexNumberTemp
            else:
                srcEthernet += hexNumberTemp
            srcEthernet += ":"

        
        srcEthernet = srcEthernet[0: len(srcEthernet)-1] # src ethernet
        print(srcEthernet)
        # ethernet payload of lldp
        ethernetP = ethernetH[4]
        ethernetP = lldp.unpack_lldp_frame(ethernetP)
        list_TLV = []
        for i in ethernetP:
            list_TLV.append(i)
        self.s.send(self.createLLDPPacket( srcEthernet, bytes('dpid:0000000000000001', encoding='utf-8'), list_TLV[1]))
        """

        """
        while(1):
            data = self.s.recv(self.buffer_size)
            self.s.send(self.createLLDPPacket( srcEthernet, list_TLV[0], list_TLV[1]))

        """
        """
        #b'\x64\x70\x69\x64\x3a\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x33'
        # create LLDP message
        lldp_data = lldpMsg()
        lldp_data.chassis_id = tlvLLDP(1, 7,binaryData(b'dpid:0000000000000001'))
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



if __name__ == '__main__':
    tda = Switch('192.168.0.101', 6633, 8192, '192.168.0.104')
    #tda.createOFFeatureReplyFromSnmp(111,1)
    tda.startConnectToController()
    num = input()   
    tda.stopConnectToController()



    
