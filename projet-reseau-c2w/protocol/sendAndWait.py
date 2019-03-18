#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 18:11:29 2018

@author: b18kouas
"""

from twisted.internet import reactor
import struct



import collections
class sendAndWait:
    def __init__(self):
        
      
        self.ack_recu=1
       
        self.paquet_memoire=[]
       
       
    def sendWait(self,paquet,numSeq,nbre_tentative,host_port):
        
        self.paquet_memoire.append([numSeq,paquet,nbre_tentative,host_port])
        (Type,numberSeq,longueur,messageTotal)=self.c2wUdpChatClientProtocol.PaquetRecu(self.paquet_recu)
        if Type==0:
            reactor.callLater(1,self.traitemenAck,numberSeq)
            
        
        
        
    
    def send(self,message,host_port):
        for p in self.paquet_memoire:
	  if (p[4]==host_port):   
             if (p[1] <= 7):
                 if (p[2] == 0):
                      print('host-port envoi est:'+str(type(host_port)))
                      self.transport.write(message,host_port)
                      p[1]+=1
                      print('nombre de message envoye:'+str(p[1]))
                      
                      
                 elif(p[2] == 1):
                       print('Le paquet a ete aquitte')  
                       self.paquet_memoire.remove(p)
               
             else:
                    print('Le paquet envoye est perdu')
                    self.paquet_memoire.remove(p)
               
  
             pass
    
    
    def traitementAck(self,numSeq):
       
             for p in self.paquet_memoire:
                  if (p[0]==numSeq):
                         p[2]=1
                         print('ack envoye par le serveur')
                         
      
     
        
       
              
             pass
            
            
    
        
       
