# coding: utf-8

########################################
# 約定したデータはここに突っ込んでおく #
# 決済の時に使うデータ                 #
########################################

class orderInfo():
    def __init__(self, id, price):
        self.id = id
        self.price = price

    def getId(self):
        return int(self.id)

    def getPrice(self):
        return self.price        
 

