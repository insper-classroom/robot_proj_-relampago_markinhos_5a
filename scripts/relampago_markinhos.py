#! /usr/bin/env python3
# -*- coding:utf-8 -*-

from __future__ import print_function, division
import rospy
import numpy as np
import tf
import aux
import math
from math import pi
import cv2
import cv2.aruco as aruco
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from tf import transformations
from tf import TransformerROS
import tf2_ros
from geometry_msgs.msg import Twist, Vector3, Pose, Vector3Stamped
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from std_msgs.msg import Header

from ros_functions import RosFunctions
from ros_actions import RosActions
from garra import Garra
from estacao import Estacao

from prints import encerrar_missao
from termcolor import colored

class RelampagoMarkinhos:

    def __init__(self, objetivo, creeper, conceitoC = False):
        rospy.init_node("projeto")

        self.objetivo = objetivo
        self.conceitoC = conceitoC
        self.creeper = creeper
        self.dic = {}


        self.functions = RosFunctions(objetivo)
        self.actions = RosActions(self.functions)
        self.estacao = Estacao(objetivo)
        self.garra = Garra(self.actions)


        self.FLAG = 'segue_pista'      
        self.creeper_atropelado = False
        self.momento_garra = 0


        self.dic['mobilenet'] = False

        self.posicao0 = None
        self.angulo0 = None

        self.iniciar_missao() 


    ##======================== GETTERS =========================##
    def get_dic(self):
        # Getter do dicionário de variáveis desta classe
        return self.dic

    def pegar_creeper(self, dic_functions, centro, maior_contorno_area, media): 
        v_lin = 0.1
        print(dic_functions['distancia_frontal'] )
        if 0.25 < dic_functions['distancia_frontal'] < 0.28:
            self.garra.abrir_garra()

        if dic_functions['distancia_frontal'] < 0.25:
            v_lin = 0.04

        if dic_functions['distancia_frontal'] <= 0.16 and not self.creeper_atropelado:
            print('PAROU')
            self.momento_garra = rospy.get_time()
            self.creeper_atropelado = True

        if maior_contorno_area > 700 and not self.creeper_atropelado:
            if len(centro) != 0 and len(media) != 0:
                if centro[0] -15 < media[0] < centro[0] + 15:
                    self.actions.set_velocidade(v_lin)
                else: 
                    delta_x = centro[0] - media[0]
                    max_delta = 150
                    w = (delta_x/max_delta)*0.10
                    self.actions.set_velocidade(v_lin,w)
                    
        if self.creeper_atropelado:
            print('oie 5')
            self.actions.set_velocidade()
            self.FLAG = self.garra.capturar_objeto(self.momento_garra)      


    def cacador_creeper(self):
        dic_functions = self.functions.get_dic()
        img = self.functions.get_camera_bgr()
        if img is not None:
            centro, maior_contorno_area, media = self.creeper.identifica_creepers(self.functions)
            if (maior_contorno_area > 700 or self.FLAG == 'pegando_creeper') and self.FLAG != 'creeper_capturado':
                print('oie 1')
                if self.posicao0 is None:
                    self.posicao0 = dic_functions["posicao"]
                    self.angulo0 = dic_functions["ang_odom"]
                    print(colored(" - 'Relâmpago Markinhos': Localizei o Alvo!","red"))
                    print('Posição salva: ',self.posicao0,self.angulo0)
                self.FLAG = 'pegando_creeper'
                self.pegar_creeper(dic_functions,centro, maior_contorno_area, media)
           
            elif self.FLAG == 'segue_pista':
                print('oie 2')
                self.actions.segue_pista()

            elif self.FLAG == 'creeper_capturado':
                print('oie 3')
                self.FLAG = self.actions.retorna_pista(self.posicao0, self.angulo0)

    def encontrar_estacao(self):
        img = self.functions.get_camera_bgr()
        self.dic['mobilenet'] = True
        self.actions.segue_pista()
        self.estacao.estacao_objetivo(img)

    def missao_conceito_c(self):        
        # self.actions.segue_pista()
        self.encontrar_estacao()      
        self.cacador_creeper()       


        
    def iniciar_missao(self):
        try: 
            while not rospy.is_shutdown():
                if self.conceitoC:
                    self.missao_conceito_c()
                else:
                    print('Eu sou a velocidade...')

            rospy.sleep(0.01)

        except rospy.ROSInterruptException:
            encerrar_missao()