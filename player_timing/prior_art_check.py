"""Elementary rational counterexample: Nash efficiency is not equal utility."""
from fractions import Fraction as F
import json


def check():
    x=F(1,4);y=1-x;q1=1+x;q2=1+2*y
    assert x+y==1 and q1==F(5,4) and q2==F(5,2)
    assert q1/(q1+q2)==F(1,3)<F(1,2)
    for k in range(1001):
        a=F(k,1000)
        product=(1+a)*(3-2*a)
        assert product==F(25,8)-2*(a-F(1,4))**2
        assert product<=q1*q2
    return {'allocation':[str(x),str(y)],'quality':[str(q1),str(q2)],
            'product':str(q1*q2),'first_share':str(q1/(q1+q2)),
            'polynomial_identity_checks':1001,'new_theorem':False}


if __name__=='__main__':print(json.dumps(check(),sort_keys=True))
