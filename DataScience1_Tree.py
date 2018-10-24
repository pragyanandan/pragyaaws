# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sklearn
from sklearn import tree
    
x = [[181,85,10],[177,81,9],[155,71,7],[175,79,9],[147,64,5],[150,65,6],[148,56,5],[145,65,6],
     [165,71,8],[150,65,6],[143,54,5]]

y = ['male','male','female','male','female','female','female','female','male','female','female']

clf = tree.DecisionTreeClassifier()

clf = clf.fit(x,y)

predection = clf.predict ([[143,56,6]])

print(predection)