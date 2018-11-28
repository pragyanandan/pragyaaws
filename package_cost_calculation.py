

SL = 200
SW = 300
SH = 150
ML = 300
MW = 400
MH = 200
LL = 400
LW = 600
LH = 250
allowed_weight = 25
scost = 5.0
mcost = 7.5
lcost = 8.5


Package_length = int(input("enter length  :   "))
Package_Width = int(input("enter width  :   "))
Package_Height = int(input("enter Height  :   "))
Package_Weight = int(input("enter weight in KG :  "))


def return_package_cost(Package_length, Package_Width, Package_Height, Package_Weight) :
    if Package_Weight > allowed_weight:
        return 0
    else:
        if (Package_length <= SL) and (Package_Width <= SW) and (Package_Height <= SH):
           return scost
        elif (Package_length <= ML) and (Package_Width <= MW) and (Package_Height <= MH):
            return mcost
        elif (Package_length <= LL) and (Package_Width <= LW) and (Package_Height <= LH):
            return lcost
        else:
            return 100


print (return_package_cost(Package_length, Package_Width, Package_Height, Package_Weight))
