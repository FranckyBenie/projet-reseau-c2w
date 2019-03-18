# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_server_protocol')

from twisted.internet import reactor
import struct
import re
from c2w.main.constants import ROOM_IDS
class c2wTcpChatServerProtocol(Protocol):

    def __init__(self, serverProxy, clientAddress, clientPort):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param clientAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param clientPort: The port number used by the c2w server,
            given by the user.

        Class implementing the TCP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: clientAddress

            The IP address of the client corresponding to this 
            protocol instance.

        .. attribute:: clientPort

            The port number used by the client corresponding to this 
            protocol instance.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.

        .. note::
            The IP address and port number of the client are provided
            only for the sake of completeness, you do not need to use
            them, as a TCP connection is already associated with only
            one client.
        """
        #: The IP address of the client corresponding to this 
        #: protocol instance.
        self.clientAddress = clientAddress
        #: The port number used by the client corresponding to this 
        #: protocol instance.
        self.clientPort = clientPort
        #: The serverProxy, which the protocol must use
        #: to interact with the user and movie store in the server.
        self.serverProxy = serverProxy
        
        # numero de sequence du paquet courant
        self.numeroSeq_courant=0
        
        # numero de sequence du paquet qu'on a envoyé en dernière position
        self.numeroSeq_Prec=0
        
        # pour gerer la connexion et la deconnexion
        self.connexion=0 
        
        # variable pour verifier l integrité des paquets recu
        self.datagram=b''
        
        # nom de l utilisateur
        self.username=''
               
        #on garde dans cette liste tous les paquets envoyés jusqu'a obtention de leur ack
        self.paquet_memoire_ser=[]
        
        self.numSequence=0
        
        
        
        
        
        
        
    #--------------------------------------------------------------------------
    # Fonction pour gerer les numeros de sequence       
    #--------------------------------------------------------------------------

    def NumSeq (self,numSeq):

        #on genere un numero de sequence pour chaque paquet envoyé
        #il est initialisé à 0 et incremente de 1 a chaque nouvel envoi
        #jusqu'a 8191 où il revient à 0
  
        if numSeq==4095:
            numSeq=0
        else: 
            numSeq+=1
        return numSeq

    
    #--------------------------------------------------------------------------
    # Fonction pour definir le foramts des paquets d'Ack       
    #-------------------------------------------------------------------------- 

    def FormatAck(self,Type,numSeq):
        longueur=4
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)
        return(paquet)
     

    #--------------------------------------------------------------------------
    # Fonction pour recuperer les inforamtions des paquets recu      
    #-------------------------------------------------------------------------- 

    def PaquetRecu(self, datagram):
        print(datagram)
        (entete,messageTotal)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)
        entete1=entete >> 28
        Type=entete1 & int('1111',2)
        entete2=entete >>  16
        numSeq=entete2 & int('0000111111111111',2)
        longueur=entete & int('1111111111111111',2)        
        return(Type, numSeq, longueur,messageTotal)

  
    #--------------------------------------------------------------------------
    # Fonction pour definir le format du paquet Acceptation de connexion      
    #--------------------------------------------------------------------------      
    
    def paquetConRes(self,Type,numSeq):
        self.numeroSeq_courant=numSeq
        longueur=4   
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)
        return(paquet)
        
        
    #--------------------------------------------------------------------------
    # Fonction pour definir le format du paquet Refus de connexion      
    #--------------------------------------------------------------------------
            
    def paquetConEchouee(self,Type,numSeq):
        self.numeroSeq_courant=numSeq
        longueur=4   
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)
        return(paquet)

        
    #--------------------------------------------------------------------------
    # Fonction pour recuperer les donnees du nouvel utilisateur       
    #--------------------------------------------------------------------------       

    def userData(self,datagram):
        (entete,userName)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)
        userName=userName.decode('utf-8')      
        print(userName)
        return(userName)
        
        
    #--------------------------------------------------------------------------
    #Fonction pour envoyer la liste des videos disponibles       
    #--------------------------------------------------------------------------    
    
    # fonction pour former le paquet de la liste des videos disponibles
    def PaquetListMovie(self):   
        movieNombre=0
        paquetMovie=bytes()
        for movie in self.serverProxy.getMovieList():
            movieIP=self.serverProxy.getMovieAddrPort(movie.movieTitle)[0]
            moviePort=self.serverProxy.getMovieAddrPort(movie.movieTitle)[1]
            movieName=movie.movieTitle
            movieLong=len(movieName)
            movieIP=re.findall(r"\d+",movieIP)
            print('Movie:'+str(movieLong)+','+movieName+','+str(movieIP)+','+str(moviePort))                                       
            formatIP=(int(movieIP[0])<<24)+(int(movieIP[1])<<16)+(int(movieIP[2])<<8)+(int(movieIP[3]))
            movieNombre+=1
            paquetMovie+=struct.pack('!B'+str(len(movieName.encode('utf-8')))+'sIH',len(movieName.encode('utf-8')),movieName.encode('utf−8'),formatIP,moviePort)       
        paquetTotal=paquetMovie
        return(paquetTotal)
           
    # fonction pour former le paquet total de la liste des videos (entete+liste)
    def EnvoiListMovie(self,Type,numSeq):
        self.numeroSeq_courant=numSeq
        movies=self.PaquetListMovie()
        longueur=len(movies)+4        
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)+movies
        return(paquet)   
                     
    #--------------------------------------------------------------------------
    #Fonction pour envoyer la liste des utilisateurs        
    #--------------------------------------------------------------------------
    
    # fonction pour former le paquet de la liste des utilisateurs
    def ListUser(self,room):
        paquetUserA=bytes()     
        paquetUserM=bytes()  
        paquetUserMovie=bytes()
        userNombreA=0
        userNombreM=0   
        if room==ROOM_IDS.MAIN_ROOM :
            for user in self.serverProxy.getUserList():                              
                if(user.userChatRoom==ROOM_IDS.MAIN_ROOM):                   
                    statut=0
                    usernameA=user.userName
                    userNombreA=userNombreA+1                                       
                    paquetUserA+=struct.pack('!B'+str(len(usernameA.encode('utf−8')))+'sB', len(usernameA.encode('utf−8')),usernameA.encode('utf−8'),statut)   
                else:                    
                    statut=1
                    usernameM=user.userName
                    userNombreM=userNombreM+1                   
                    paquetUserM+=struct.pack('!B'+str(len(usernameM.encode('utf−8')))+'sB', len(usernameM.encode('utf−8')),usernameM.encode('utf−8'),statut)   
            userNbre=userNombreA+userNombreM
            print('Le nombre d utilisateur est:'+str(userNbre))  
            paquetUser=paquetUserA+paquetUserM                  
            return( paquetUser) 
        elif room!=ROOM_IDS.MAIN_ROOM :
            for user in self.serverProxy.getUserList():         
                if (user.userChatRoom==room ):
                    statut=1
                    usernameMovie=user.userName
                    paquetUserMovie+=struct.pack('!B'+str(len(usernameMovie.encode('utf−8')))+'sB', len(usernameMovie.encode('utf−8')),usernameMovie.encode('utf−8'),statut)   
            return( paquetUserMovie) 
        
         
        
     
    # fonction pour former le paquet total de la liste des utilisateurs (entete+liste)      
    def EnvoiUser(self,Type,numSeq,room):
        self.numeroSeq_courant=numSeq
        users=self.ListUser(room)
        longueur=len(users)+4
        entete=(Type<<28)+(numSeq<<16)+longueur 
        paquet=struct.pack('!I',entete)+users    
        return(paquet)
                
  
    #--------------------------------------------------------------------------
    # Fonction pour les messages      
    #--------------------------------------------------------------------------    

    # fonction pour envoyer un message
    def EnvoiMsg(self,Type,numSeq,username,message):
        paquetMes=struct.pack('!B'+str(len(username.encode('utf−8')))+'s'+str(len(message.encode('utf−8')))+'s',len(username.encode('utf−8')),username.encode('utf−8'),message.encode('utf−8'))
        longSpeudo=len(username.encode('utf−8'))
        longMsg=len(message.encode('utf−8'))     
        self.numeroSeq_courant=numSeq        
        longueur=longSpeudo+longMsg+1+4        
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)+paquetMes
        print('la paquet est:'+str(paquet))
        return(paquet) 
        
        
    # fonction pour recuperer les informations lorsqu on recoit un message   
    def MsgRecu(self,datagram):
        (entete,messageTotal)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)        
        longueur=entete & int('1111111111111111',2)       
        datagram=datagram[4:]
        longMes=longueur-4        
        longName=struct.unpack('!B',datagram[0:1])[0]
        datagram=datagram[1:]
        user_name=struct.unpack(str(longName)+'s',datagram[0:longName])[0]
        user_name=user_name.decode('utf-8') 
        datagram=datagram[longName:]
        longMessage=longMes-1-longName              
        message=struct.unpack(str(longMessage)+'s',datagram[0:longMessage])[0]
        message=message.decode('utf-8')
        return(user_name,message)
        
        
        
    #--------------------------------------------------------------------------
    # Fonction pour gerer le protocole send & wait    
    #--------------------------------------------------------------------------
    
    # fonction pour verifier si on a recu un ack
    def traitementAck(self,numSeq,host_port):      
        for p in self.paquet_memoire_ser:                  
            if (p[4]==host_port):
                if (p[0]==numSeq):                        
                    p[2]=1                         
                    print('ack envoye par le serveur')

    #fonction pour envoyer le paquet si jamais on a toujours pas recu d ack
    def sendAndWait(self,host_port):   
      for p in self.paquet_memoire_ser:            
          if (p[4]==host_port):                  
              if (p[1] <= 7):
                  if (p[2] == 0):                           
                      self.transport.write(p[3])
                      p[1]+=1
                      print('nombre de message envoye:'+str(p[1]))
                      reactor.callLater(1,self.sendAndWait,p[4])
                            
                  elif(p[2] == 1):
                      print('avant',self.paquet_memoire_ser)
                      print('Le paquet a ete aquitte',p[0])  
                      self.paquet_memoire_ser.remove(p) 
                      print('apres',self.paquet_memoire_ser)                        
              else:
                  print('nombre de message envoye:'+str(p[1]))          
                  for user in self.serverProxy.getUserList():
                      if(user.userAddress==host_port):
                          self.serverProxy.updateUserChatroom(self.serverProxy.getUserByAddress(host_port).userName,ROOM_IDS.OUT_OF_THE_SYSTEM_ROOM)
                          self.serverProxy.removeUser(self.serverProxy.getUserByAddress(host_port).userName)                              
                          print('l utilisateur a ete supprimé ')
                          self.paquet_memoire_ser.remove(p)  
                               
                          # on informe les autres utilisateurs
                          for user in self.serverProxy.getUserList():                                                                                                   
                              paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,ROOM_IDS.MAIN_ROOM)                                   
                              self.paquet_memoire_ser.append([user.userChatInstance.numSequence+1,1,0,paquet,user.userAddress])
                              user.userChatInstance.transport.write(paquet)
                              reactor.callLater(1,self.sendAndWait,user.userAddress)
                              print('Le paquet envoye est perdu')
          break

      
    def dataReceived(self,data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """
           
        self.datagram=self.datagram+data
        print('data recue'+str(self.datagram))
        # on verifie si l integrité du paquet recu             
        if(len(self.datagram)>=4):
            (Type,numSeq,longueur,messageTotal)=self.PaquetRecu(self.datagram)                         
            if(len(self.datagram)==longueur):               
                print('paquet recu sans perte')              
                self.reponse_requet(self.datagram)
                self.datagram=b''

        pass
        
    
    #--------------------------------------------------------------------------
    # Fonction pour faire les traitements en fonction des paquets recu  
    #-------------------------------------------------------------------------- 
    
    def reponse_requet(self, data):
                
        host_port=(self.clientAddress,self.clientPort)       
        print(" ".join("{:02x}".format(c) for c in data))
        (Type, numSeq, longueur,messageTotal)=self.PaquetRecu(data)
        
    # on met a jour les numeros de sequences dans la liste des utilisateurs 
        if (Type!=0 and Type!=1):
            for u in self.serverProxy.getUserList():
                if (u.userAddress==host_port):
                    u.userChatInstance.numSequence=numSeq
            
     #-------------------------------------------------------------------------  
     #on a recu un ack
     
        if (Type==0):            
            for user in self.serverProxy.getUserList(): 
                self.traitementAck(numSeq,user.userAddress)
                if(user.userAddress==host_port):                     
                    user.userChatInstance.numSequence=numSeq
                    if (self.numeroSeq_Prec==numSeq):
                        if (user.userChatInstance.numSequence ==numSeq) :
                            user.userChatInstance.ack_recu=1
                            print('ack envoye par le client')                                                         
                             
                    else:
                        user.userChatInstance.ack_recu=0   
      
     #-------------------------------------------------------------------------
     # on envoie un ack au client      
                 
        if(Type!=0):  
            print('message recu')
            ack=self.FormatAck(0,numSeq)
            print('ack envoyé au client:'+str(ack))
            self.transport.write(ack)
            print('ack bien envoyé au client avec seqnum:'+str(numSeq))
           
      #------------------------------------------------------------------------
      # on a recu une requete de connexion   
      
        if(Type==1 or Type==0):
            
            # on traite cette requete
            # on verifie le nom du client
            if (Type==1):
                userName=self.userData(data)
                self.username=userName           
                print('username test:'+str(userName))                 
                # s il depasse le nombre de caractere permis, on lui envoie un message d erreur
                if(len(userName)>251):
                    print('pseudo trop long')
                    paquet=self.paquetConEchouee(9,0)                                        
                    self.transport.write(paquet)                                                  
                    self.connexion=1
                                
                # si le nom existe deja un lui envoie un message d erreur
                elif(self.serverProxy.userExists(str(userName))):                      
                    paquet=self.paquetConEchouee(9,0)                                              
                    self.transport.write(paquet)                                                                 
                    self.connexion=1
                                
                 # sinon on accepte la demande de connexion
                elif not(self.serverProxy.userExists(str(userName))):
                     self.connexion=0
                     print('pseudo correct:connexion accepté')                      
                     self.serverProxy.addUser(userName,ROOM_IDS.MAIN_ROOM,self,host_port)
                      
                      
                     for user in self.serverProxy.getUserList():
                         if (user.userAddress==host_port):  
                             paquet=self.paquetConRes(8,0) 
                             self.paquet_memoire_ser.append([0,1,0,paquet,host_port])
                             self.numeroSeq_Prec=self.numeroSeq_courant
                             self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)                      
                             self.transport.write(paquet)
                             reactor.callLater(1,self.sendAndWait,host_port)                     
                             print('requete de connexion')
                             for user in self.serverProxy.getUserList() :
                                 print('les users sont',user)
                              
                     if(len(self.serverProxy.getUserList())>0):
                         newConnect = self.serverProxy.getUserByAddress(host_port).userName
                         print('le nouveau connecté est:',newConnect)
                           
                           # on fait une mise a jour
                         for user in self.serverProxy.getUserList() :                               
                             if(user.userChatRoom == ROOM_IDS.MAIN_ROOM) :                                        
                                 if not (user.userName ==newConnect ) :                                                                                       
                                     if not (user.userAddress==host_port):                                                                                                                                                                                                   
                                         print('numero de sequence partant'+str(user.userChatInstance.numSequence+1))
                                         numero=user.userChatInstance.numSequence+1
                                         paquet=self.EnvoiUser(6,numero,ROOM_IDS.MAIN_ROOM)
                                         self.paquet_memoire_ser.append([user.userChatInstance.numSequence+1,1,0,paquet,user.userAddress])
                                         print('Tu la recu avec numSEq:'+str(user.userChatInstance.numSequence+1))
                                         user.userChatInstance.transport.write(paquet) 
                                         reactor.callLater(1,self.sendAndWait,user.userAddress)
                                                         
            
            if (Type==0):           
                if (numSeq==0 and self.connexion!=1):                          
                    paquet=self.EnvoiUser(6,1,ROOM_IDS.MAIN_ROOM)
                    self.paquet_memoire_ser.append([1,1,0,paquet,user.userAddress])                    
                    self.numeroSeq_Prec=self.numeroSeq_courant
                    self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)   
                    self.transport.write(paquet)
                    reactor.callLater(1,self.sendAndWait,user.userAddress)
                                      
                # on envoie au nouveau connecté la liste des videos disponibles
                if (numSeq==1 and self.connexion!=1):
                    paquet=self.EnvoiListMovie(5,2)
                    self.paquet_memoire_ser.append([2,1,0,paquet,user.userAddress])
                    self.numeroSeq_Prec=self.numeroSeq_courant
                    self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)   
                    self.transport.write(paquet)
                    reactor.callLater(1,self.sendAndWait,user.userAddress)
               
       #-----------------------------------------------------------------------
       # on a recu une requete pour acceder a un film             
        if (Type==2):
            roomName=messageTotal.decode('utf-8')                           
            user=self.serverProxy.getUserByAddress(host_port)
            username=user.userName
            if(user.userChatRoom==ROOM_IDS.MAIN_ROOM):
                  print('film a watch:'+roomName)
                  self.serverProxy.startStreamingMovie(roomName)
                  username = self.serverProxy.getUserByAddress(host_port).userName
                  self.serverProxy.updateUserChatroom(username,roomName)
                  for user in self.serverProxy.getUserList():
                      if (user.userName==username):
                          user.userChatRoom=roomName
                                          
                  # on fait une mise a jour
                  for user in self.serverProxy.getUserList():
                      if(user.userChatRoom == ROOM_IDS.MAIN_ROOM) :
                          if not (user.userName==username):                                         
                              print('mise a jour Main Room pour go to movie')                                                                                                                           
                              paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,ROOM_IDS.MAIN_ROOM)                                      
                              user.userChatInstance.transport.write(paquet)                                                                                                                    
                                     
                                       
                      elif (user.userChatRoom==roomName):                                    
                          print('mise a jour Movie Room pour go to movie')                                                              
                          paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,roomName)                          
                          user.userChatInstance.transport.write(paquet)                                                                   
                   
                  
     #-------------------------------------------------------------------------
     # on a recu une requete pour quitter la movie room          
                  
        if (Type==3):
            user=self.serverProxy.getUserByAddress(host_port)
            print(user.userChatRoom)
            roomName=self.serverProxy.getUserByAddress(host_port).userChatRoom
            username = self.serverProxy.getUserByAddress(host_port).userName
            if(user.userChatRoom!=ROOM_IDS.MAIN_ROOM):
                self.serverProxy.stopStreamingMovie(user.userChatRoom)
                username = self.serverProxy.getUserByAddress(host_port).userName
                self.serverProxy.updateUserChatroom(username,ROOM_IDS.MAIN_ROOM) 
                for user in self.serverProxy.getUserList():
                    if (user.userName==username):
                        user.userChatRoom=ROOM_IDS.MAIN_ROOM
                for user in self.serverProxy.getUserList() :
                    if(user.userChatRoom == ROOM_IDS.MAIN_ROOM) :                                       
                        print('mise a jour Main Room pour go to main room')        
                        paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,ROOM_IDS.MAIN_ROOM)                                                              
                        user.userChatInstance.transport.write(paquet)                                     
                    elif (user.userChatRoom==roomName):
                        if not (user.userName==username):                                     
                            print('mise a jour Movie Room pour go to main room')
                            paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,roomName)                                                                     
                            user.userChatInstance.transport.write(paquet)
                                                  
            print('quitte la moovie room')
                   
                   
        #----------------------------------------------------------------------
        # on a recu un message
        # on l envoie donc aux utilisateurs se trouvant dans la meme chambre que l emetteur    
        
        if(Type==7):                      
            (userNom,message)=self.MsgRecu(data)
            emetteurMsg = self.serverProxy.getUserByAddress(host_port)    
            print('weeeeeeeeeeeee',emetteurMsg)
            print('message recu:'+str(message))
            for user in self.serverProxy.getUserList() :
                if(user.userChatRoom == emetteurMsg.userChatRoom) :
                    if not (user.userName==emetteurMsg.userName):
                        print('user envoyant le msg:'+str(emetteurMsg.userName))                                                                                                                                                                  
                        print('le msg est:'+str(message))
                        paquet=self.EnvoiMsg(7,user.userChatInstance.numSequence+1,userNom,message)                        
                        user.userChatInstance.transport.write(paquet)                                                        
                            
                          
       #-----------------------------------------------------------------------
       # on a recu une requete de deconnexion  
                              
        if (Type==4):
            user = self.serverProxy.getUserByAddress(host_port)            
            if(user.userChatRoom==ROOM_IDS.MAIN_ROOM):
                self.user_adress= user.userAddress                                 
                self.serverProxy.updateUserChatroom(user.userName,ROOM_IDS.OUT_OF_THE_SYSTEM_ROOM) 
                self.serverProxy.removeUser(self.serverProxy.getUserByAddress(host_port).userName)  
                print('Deconnexion du syteme')  
                  
                # on fait une mise a jour
                for user in self.serverProxy.getUserList() :                                          
                    if(user.userChatRoom == ROOM_IDS.MAIN_ROOM) :                                  
                        paquet=self.EnvoiUser(6,user.userChatInstance.numSequence+1,ROOM_IDS.MAIN_ROOM)
                        self.paquet_memoire_ser.append([user.userChatInstance.numSequence+1,1,0,paquet,user.userAddress])
                        user.userChatInstance.transport.write(paquet,)
                        reactor.callLater(1,self.sendAndWait,user.userAddress) 
        pass