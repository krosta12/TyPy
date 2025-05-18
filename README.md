# WELCOME
##### Lihtne interpriteeruv prograamilise keelt Pythoni baasil
<img src="https://github.com/krosta12/TyPy/blob/master/assets/logo.png" width="50%" />

# KIRJELDUS
##### See projekt luuab uued konstruktsiooni pythonisse kasutades oma iterpretaator pythonisse. Projekt lisab best praktisi Type Scriptist ja Java-st.

# UUED VÕIMALUSED

### USE STRICT:
##### ```use strict``` - instruktsioon mis nõuab kasutada muutujade ja funktsioonide annotatsioonid.
##### Kirjutatakse dokumendi algusel
#### Kus reziim nõuab kasutada
```py
x = 5 #tekkib viga
int x = 5
#või
x: int = 5
```
##### asemel.

##### Saamaselt nagu muutujadega vaja teha annotatsioonid funktsiooni defineerimiseks
#### Ilma ```use strict```
```py
def say_hi(to):
    print("hello " + to)
```

#### Kasutades ```use strict```
```py
use strict

def say_hi(to: str) -> None:
    print("hello " + to)
```
##### Annotatioon ```str``` enne ```to``` nõuab seda, et funktsiooni argument oleks ainult ```str``` andmestruktuurina. 
##### Annotation ```None``` pärast funktsiooni argumentide listi märastb mida pead kfunktsioon tagastama.  ```None``` on erijuht mis ei nõua ```return``` statementi. Kuid teised ```auto```, ```int```, ```str```... nõuvad ```return``` tapselt saamase andmetüüpiga.

#### Vigane funktsiooni keha ```return``` puudub
```py
use strict

def say_hi(to: str) -> str:
    print("hello " + to)

print(say_hi("jockii druce"))
#tuleb 'none-return statement'
```
#### Vigane annatatsiooni näide
```py
def say_hi(to: str) -> int: # pidi int tagastama
    return "hello " + to # tagastame str

print(say_hi("jockii druce")) #saame vigu
```
***Õige annatatsiooni kasutus***
```py
use strict

def say_hi(to: str) -> str: #õige argumendi tüüp
    return "hello " + to # on olemas return && type(return) on õige andmestruktuuriga

print(say_hi("jockii druce"))
```


## AUTO
#### Kuna Pythonis kõik andmestruktuurid on tuletatud object klaasist.

##### Siis oli lisatud ```auto``` võtmesõna mis teeb lihtsemaks annatatsioonide loomine.
```py
x: Class_Name = Class_Name() #on raske
x: auto = Class_Name() #lihtsam
x: auto = server.get_rq("GET", "...")
```

## READONLY
#### Konstantiid võtmesõnaga ```readonly``` mis pärast defineerimist pole võimalik muuta või üledefineerida
**Süntaks**  
```py
readonly pi: float = 3.14
pi = 3.143 # tuleb viga!
```

## AS
##### ```as``` — tüübidüstoopia või tüübiassertsiooni operaator 
#### TyPy võimaldab sõna `as` kasutada, et teha jooksvalt tüübiassertsioone ilma eraldi funktsiooni või dekoratsioonita:
```py
x = some_expr as TargetType
```

## INTERFACE SYSTEM
### INTERFACE
##### Laseb kasutada võtmesõna ```interface``` muutujade ja funktsiooni nimide ette kirjutamiseks.
```py
interface Point:
    x: int,
    y: int
    def väljasta_koordinaatid() -> None: pass
```
### IMPLEMENTS
##### Vigane implementatsiooni näide
```py
interface PointMathFuncs:
    def get_point_x_cord() -> float: pass
    def get_point_y_cord() -> float: pass

class Line implements PointMathFuncs:
    def __init__(self,x:float,y:float) -> None:
        self.x: float = x
        self.y: float = y
        def get_point_x_cord() -> float:
            return x
        #viga!
        #class Line ei realiseeri PointMathFuncs inteface
```
##### Õige näide
```py
use strict

interface PointMathFuncs:
    def get_point_x_cord() -> float: pass
    def get_point_y_cord() -> float: pass

class Line implements PointMathFuncs:
    def __init__(self,x:float,y:float) -> None:
        self.x: float = x
        self.y: float = y
        def get_point_x_cord() -> float:
            return x
        def get_point_y_cord() -> float:
            return y
```


## ENUM
##### On lisatud võtmesõna ```enum``` kahe konstruuktoriga

```py
use strict

enum ex1:
    one :int,
    two :int

enum ex:
    one : int = 3,
    two : int = 4
```

##### Enum standartselt itereritatakse väärtusi järgi. Võimalik itereerida nagu "võtti" - "väärtusi"
```py
for element in ex1:
    print(str(element.name) + ": " + str(element.value))
```

## TYPE ALIAS
##### Laseb defineerida oma andmestruktuurid objekti baasil
```py
type my_int_type = int
```
#### On ka võimalik defineerida kergerid andmestruktuurid
```py
use strict

type user:
    userId: int
    userName: str

def make_user() -> user:
    return {
        "userId": 1,
        "userName": "Alice",
    }

user: auto = make_user()
print(user)
```

## OPTIONAL
#### optional muutujade süsteem kasutades võtmesõna ```?```. Kasutatakse muutujade defineerimiseks kus ei pea olema väärtust.

## PRIVAATSUS
##### privaatsuse piirkonnad kasutades võtmesõnad - ```public```, ```protected```, ```private```. Saama reeglidega mis kasutatakse Javas või C-taolised P. keeled.

### Kus pärast defineerimist, väljadele juurdepääseks kasutatakse reeglid:
##### ```private```: pärast defineerimist, võimalik muutujad kutsuda kasutades ```__``` muutuja nime enne
##### ```protected```: pärast defineerimist, võimalik muutujad kutsuda kasutades ```_``` muutuja nime enne
##### ```public```: pärast defineerimist, kutsumine toimub standartse viisil
