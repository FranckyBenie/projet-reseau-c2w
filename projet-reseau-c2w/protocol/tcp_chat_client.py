# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
import struct
logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')
from twisted.internet import reactor
from c2w.main.constants import ROOM_IDS


class c2wTcpChatClientProtocol(Protocol):

    def __init__(self, clientProxy, serverAddress, serverPort):
        """
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: serverAddress

            The IP address of the c2w server.

        .. attribute:: serverPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """

        #: The IP address of the c2w server.
        self.serverAddress = serverAddress
        #: The port number used by the c2w server.
        self.serverPort = serverPort
        #: The clientProxy, which the protocol must use
        #: to interact with the Graphical User Interface.
        self.clientProxy = clientProxy
        
        # variable pour verifier l integrité des paquets recu
        self.datagram=b''
        
        #room dans laquelle l utilisateur se trouve
        self.room= ''
        
        #numero de sequence du paquet envoyé lorsqu'on veut acceder a une movie room
        self.numeroSeq_GoToMovie=0
        
        #numero de sequence du paquet envoyé lorqu on veut quitter la movie room
        self.main_rome=0
        
        #variable pour recuperer le nom du film de l utilisateur lorqu il accede a la movie room
        self.roomName=''
        
        #numero de sequence du paquet envoyé lorsqu'on veut se deconnecter du système
        self.deconnexion=0
        
        #on garde dans cette liste tous les paquets envoyés jusqu'a obtention de leur ack
        self.paquet_memoire=[]
        
        
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
    # Fonction pour definir les formats de paquet       
    #--------------------------------------------------------------------------      

    def FormatPaquet(self,Type,numSeq,longueur,messageTotal):
        longueur=len(messageTotal)
        entete=(Type<<12)+(numSeq<<16)+longueur
        paquet=struct.pack('!II'+str(len(messageTotal))+'s',entete, messageTotal.encode('utf−8'))
        return(paquet)



    #--------------------------------------------------------------------------
    # Fonction pour definir le format de qu paquet de login       
    #--------------------------------------------------------------------------   

    def PaquetLogin(self,Type,numSeq,userName):
        self.numeroSeq_courant=numSeq       
        userNamepack=struct.pack(str(len(userName.encode('utf−8')))+'s', userName.encode('utf−8'))
        longueur=len(userNamepack)+4
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)+userNamepack  
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
    # Fonction pour definir le foramts des paquets d'Ack       
    #--------------------------------------------------------------------------          

    def FormatAck(self,Type,numSeq):
        longueur=4
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)
        return(paquet)
        
    #--------------------------------------------------------------------------
    # Fonction pour recuperer la liste des utilisateurs de la Main Room      
    #-------------------------------------------------------------------------- 
    
    def PaquetUser(self, datagram):
        # on affiche le paquet recu
        print(" ".join("{:02x}".format(donnee) for donnee in datagram))
       
        # liste des utilisateurs du systeme
        userList=list()
        
        # liste des utilisateurs se trouvant dans la meme movie room que l utilisateur
        users_movie=list()
        
        #on separe l entete du message utile
        (entete,messageTotal)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)
        entete1=entete >> 28
        Type=entete1 & int('1111',2)
        entete2=entete >>  16
        numSeq=entete2 & int('0000111111111111',2)
        longueur=entete & int('1111111111111111',2)
        
        datagram=datagram[4:]        
        longueurMes=len(messageTotal)
        #on recupere les informations recu jusqu a ce qu il n y a plus rien dans le paquet
        while (longueurMes!=0):        
            longName=struct.unpack('!B',datagram[0:1])[0]           
            datagram=datagram[1:]                       
            user_name=struct.unpack(str(longName)+'s',datagram[0:longName])[0]          
            user_name=user_name.decode('utf-8') 
            print(user_name)
            datagram=datagram[longName:]           
            statut=struct.unpack('B',datagram[0:1])[0]                                                                
            if (statut==0):
                statutUser=ROOM_IDS.MAIN_ROOM
            else:
                statutUser=ROOM_IDS.MOVIE_ROOM
                users_movie.append((user_name,self.roomName))                                                                            
            userList.append((user_name, statutUser))
            datagram=datagram[1:]           
            longueurMes=longueurMes-(longName+len(str(statut))+len(str(longName)))
        print(userList)
        return(userList,users_movie)
        
        
    
    #----------------------------------------------------------------
    # Fonction pour la liste des videos disponibles     
    #----------------------------------------------------------------        
        
    def PaquetMovie(self, datagram):
        
       
        # liste contenant la longueur, le nom, l adresse IP et le port des films
        movieList=list()
        
        #on separe l'entete du message en lui meme
        (entete,messageTotal)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)    
        entete1=entete >> 28
        Type=entete1 & int('1111',2)
        entete2=entete >>  16
        numSeq=entete2 & int('0000111111111111',2)
        longueur=entete & int('1111111111111111',2)       
        datagram=datagram[4:]      
        longueurMes=len(messageTotal)        
        while (longueurMes>0):       
            longMovie=struct.unpack('!B',datagram[0:1])[0]            
            datagram=datagram[1:]           
            movie_name=struct.unpack(str(longMovie)+'s',datagram[0:longMovie])[0]         
            movie_name=movie_name.decode('utf-8')            
            datagram=datagram[longMovie:]
           
            # on recupere l adresse IP et le port de chaque film
            adr_ip=struct.unpack('!I',datagram[0:4])[0]
            adr_ip3 = adr_ip & 255
            adr_ip = adr_ip >> 8
            adr_ip2 = adr_ip & 255
            adr_ip = adr_ip >> 8
            adr_ip1 = adr_ip & 255
            adr_ip = adr_ip >> 8
            adr_ip0 = adr_ip
            ip_adress = str.join(".",(str(adr_ip0),str(adr_ip1),str(adr_ip2),str(adr_ip3)))
                      
            datagram=datagram[4:]
            port=struct.unpack('!H',datagram[0:2])[0]                       
            
            #on ajoute chaque film dans la movieList
            movieList.append((movie_name,ip_adress ,port))
            
            datagram=datagram[2:]
            longueurMes=longueurMes- (longMovie+(len(str(ip_adress))-3)+len(str(port))+len(str(longMovie)))           
        print(movieList) 
        return(movieList)
        
        
    
    #--------------------------------------------------------------------------
    # Fonction pour aller dans une movie room      
    #-------------------------------------------------------------------------- 
    
    def FormatSelectMovie(self,Type,numSeq,movieName):
        self.numeroSeq_courant=numSeq
        longueur=len(movieName)+4
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I'+str(len(movieName.encode('utf-8')))+'s',entete, movieName.encode('utf−8'))
        return(paquet)
        
        
     #-------------------------------------------------------------------------
    # Fonction pour quitter la salle de video     
    #-------------------------------------------------------------------------- 
    def FormatLeaveRoom(self,Type,numSeq):
        self.numeroSeq_courant=numSeq
        longueur=4  
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I', entete)
        return(paquet)
        
              
          
    #--------------------------------------------------------------------------
    # Fonction pour les messages      
    #--------------------------------------------------------------------------    
               
    # fonction pour envoyer un message 
    def EnvoiMsg(self,Type,numSeq,username,message):
        paquetMes=struct.pack('!B'+str(len(username.encode('utf−8')))+'s'+str(len(message.encode('utf−8')))+'s',len(username.encode('utf−8')),username.encode('utf−8'),message.encode('utf−8'))
        longSpeudo=len(self.username.encode('utf−8'))
        longMsg=len(message.encode('utf−8'))       
        self.numeroSeq_courant=numSeq      
        longueur=longSpeudo+longMsg+1+4        
        entete=(Type<<28)+(numSeq<<16)+longueur
        paquet=struct.pack('!I',entete)+paquetMes       
        print('la paquet est:'+str(paquet))
        return(paquet) 
               
    # fonction pour recuperer les informations lorqu on recoit un message    
    def MsgRecu(self,datagram):
        (entete,messageTotal)=struct.unpack('!I'+str(len(datagram)-4)+'s',datagram)       
        entete1=entete >> 28
        Type=entete1 & int('1111',2)
        entete2=entete >>  16
        numSeq=entete2 & int('0000111111111111',2)
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
    # Fonction pour send & wait    
    #-------------------------------------------------------------------------- 
    
    # fonction pour verifier si on a recu un ack
    def traitementAck(self,numSeq):       
        for p in self.paquet_memoire:
            if (p[0]==numSeq):
                p[2]=1
                print('ack envoye par le serveur')
                         
    #fonction pour envoyer le paquet si jamais on a toujours pas recu d ack
    def sendAndWait(self):
        for p in self.paquet_memoire:
            if (p[1] <= 7):
                if (p[2] == 0):                           
                    self.transport.write(p[3])
                    p[1]+=1
                    print('nombre de message envoye:'+str(p[1]))
                    reactor.callLater(1,self.sendAndWait)
                elif(p[2] == 1):
                    print('Le paquet a ete aquitte')  
                    self.paquet_memoire.remove(p)        
            else:
                print('Le paquet envoye est perdu')
                self.paquet_memoire.remove(p)
    

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The client proxy calls this function when the user clicks on
        the login button.
        """
        moduleLogger.debug('loginRequest called with username=%s', userName)
        print(userName)
        
        # on forme le paquet pour le requete de connexion
        paquet=self.PaquetLogin(1,0,userName)      
        
        #on sauvegarde le nom de l utilisateur lorsqu il fait une requete de connexion
        self.username=userName
        # on envoie le paquet au serveur

        #server=(self.serverAddress,self.serverPort)
        self.transport.write(paquet)
        
        #on sauvegarde le paquet envoyé
        self.paquet_memoire.append([0,1,0,paquet])
        self.numeroSeq_Prec=self.numeroSeq_courant
        self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)
         
        # on attend 1s, si on n a toujours pas recu d ack on renvoit le paquet au serveur
        reactor.callLater(1,self.sendAndWait)
        

    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called by the client proxy when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or toint(entete) the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        
        paquet=self.EnvoiMsg(7,self.numeroSeq_courant,self.username,message)      
        print(" ".join("{:02x}".format(donnee) for donnee in paquet))     
       
        # on envoie le paquet au serveur        
        self.transport.write(paquet)
        self.paquet_memoire.append([self.numeroSeq_courant,1,0,paquet])
        self.numeroSeq_Prec=self.numeroSeq_courant
        self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)
        reactor.callLater(1,self.sendAndWait)
        
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called by the client proxy  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        #pour acceder a une movie room
        if (self.room== 'main_room'):
            paquet=self.FormatSelectMovie(2,self.numeroSeq_courant,roomName)
            self.numeroSeq_GoToMovie=self.numeroSeq_courant
            self.roomName=roomName            
            self.transport.write(paquet) 
            self.paquet_memoire.append([self.numeroSeq_courant,1,0,paquet])
            self.numeroSeq_Prec=self.numeroSeq_courant
            self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)
            reactor.callLater(1,self.sendAndWait)
        
        #pour sortir de la movie room      
        elif (self.room=='movie_room'):
            paquet=self.FormatLeaveRoom(3,self.numeroSeq_courant)
            self.main_rome=self.numeroSeq_courant            
            self.transport.write(paquet) 
            self.paquet_memoire.append([self.numeroSeq_courant,1,0,paquet])
            self.numeroSeq_Prec=self.numeroSeq_courant
            self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)
            reactor.callLater(1,self.sendAndWait)
        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
        
        paquet=self.FormatLeaveRoom(4,self.numeroSeq_courant)
        self.deconnexion=self.numeroSeq_courant      
        self.transport.write(paquet) 
        self.paquet_memoire.append([self.numeroSeq_courant,1,0,paquet])
        self.numeroSeq_Prec=self.numeroSeq_courant
        self.numeroSeq_courant=self.NumSeq(self.numeroSeq_courant)      
        reactor.callLater(1,self.sendAndWait)
        pass
    
    
    
    def dataReceived(self,data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """        
              
        # on verifie si l integrité du paquet recu    
        self.datagram=self.datagram+data
        print('donnée recue'+str(self.datagram))
          
        
        while(len(self.datagram)>=4):
            (Type,numSeq,longueur,messageTotal)=self.PaquetRecu(self.datagram)
                         
            if(len(self.datagram)>=longueur):
                paquet=self.datagram[0:longueur]
                print('paquet recu sans perte')
                self.datagram=self.datagram[longueur:]                
                self.reponse_requet(paquet)
   
        pass
    
    #--------------------------------------------------------------------------
    # Fonction pour faire les traitements en fonction des paquets recu  
    #--------------------------------------------------------------------------     
   
    def reponse_requet(self, data):
        
       
        #on recupere les informations du paquet recu

        print(" ".join("{:02x}".format(donnee) for donnee in data))
        (Type,numSeq,longueur,messageTotal)=self.PaquetRecu(data)
        
     #-------------------------------------------------------------------------  
     #on a recu un ack
     
        if (Type==0):
            self.traitementAck(numSeq)
            print('ackkkkkkkkkkkkkkkkkkkkkkkkk')
            # on a recu un ack apres une requete pour acceder a la movie room
            # on rejoint donc cette movie room
            if(self.numeroSeq_GoToMovie==numSeq and numSeq>0):
                print('rejoint la movie room')
                self.clientProxy.joinRoomOKONE()
                self.numeroSeq_GoToMovie=0
                self.room='movie_room'
            
            # on a recu un ack apres un requete pour quitter la movie room
            #on rejoint donc la main room
            if(self.main_rome==numSeq and numSeq>0):
                print('sortie movie room')
                self.clientProxy.joinRoomOKONE()
                self.main_rome=0
                self.room='main_room'
            
            # on a recu un ack apres une requete pour quitter le système
            # on sort donc de l application
            if (self.deconnexion==numSeq ):
                if (self.deconnexion!=0):
                    self.clientProxy.leaveSystemOKONE()
                    print('la user est suprime')
                
     #-------------------------------------------------------------------------
     # on envoie un ack au serveur  
     
        if(Type!=0):
            print('message recu')
            ack=self.FormatAck(0,numSeq)
            print('ack envoyé au serveur:'+str(ack))
            self.transport.write(ack)
            print('ack bien envoyé au serveur avec seqnum:'+str(numSeq))
            
     #-------------------------------------------------------------------------
     # on a recu la liste des utilisateurs   
     
        if (Type==6):         
            if(numSeq==1):         
                (userList,usersMovie)=self.PaquetUser(data)           
                self.users=userList            
                print('la liste :'+str(self.users))   
                
            elif (numSeq>1):                          
                (userList,usersMovie)=self.PaquetUser(data)
                if (self.room=='main_room'):                            
                    self.clientProxy.setUserListONE(userList)                  
                elif (self.room=='movie_room'):                                
                    self.clientProxy.setUserListONE(usersMovie)
                    print('usersssssssssssssssssssss',usersMovie)
            
     #-------------------------------------------------------------------------
     # on a recu la liste des videos disponibles    
     
        if(Type==5):  
            movieList=self.PaquetMovie(data)
            print('la liste des videos est:'+str(movieList))
            print('la liste est:'+str(self.users))
            self.clientProxy.initCompleteONE(self.users,movieList)
            self.room= 'main_room'
            print(movieList)
        
        
     #-------------------------------------------------------------------------
     # on a recu un message 
     
        if(Type==7):
            (userNom,message)=self.MsgRecu(data)
            self.clientProxy.chatMessageReceivedONE(userNom, message) 
            print('le message qu on a recu est:'+str(message))
       
     #-------------------------------------------------------------------------
     #  on a recu un message d erreur apres notre requete de connexion
     
        if(Type==9):
             erreur='errreur'
             self.clientProxy.connectionRejectedONE(erreur)
        
        pass