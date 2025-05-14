WLCOME:
Lihtne interpriteeruv prograamilise keelt Pythoni baasil
...........
KIRJELDUS
See projekt luuab uued konstruktsiooni pythonisse kasutades oma iterpretaator pythonisse. Projekt lisab best praktisi Type Scriptist ja Java-st.
...........
UUED VÕIMALUSED:

...USE STRICT:
use strict - instruktsioon mis nõuab kasutada muutujade ja funktsioonide annotatsioonid.
Kirjutatakse dokumendi algusel
Kus reziim nõuab kasutada
x = 5
int x = 5
#või
x: int = 5
asemel

...AUTO:
Kuna Pythonis kõik andmestruktuurid on tuletatud object klaasist, siis oli lisatud _auto_ võtmesõna mis teeb lihtsemaks annatatsioonide loomine.
x: auto = Class_Name()
x: auto = server.get_rq("GET", "...")

...READONLY:
Konstantiid võtmesõnaga (readonly) mis pärast defineerimist pole võimalik muuta või üledefineerida
readonly pi: float = 3.14
pi = 3.143 # tuleb viga!

...AS:
as - vaja üle kirjutada

...INTERFACE SYSTEM
.....INTERFACE
Laseb kasutada võtmesõna (interface) muutujade ja funktsiooni nimide ette kirjutamiseks.
interface Point:
x: int,
y: int
def väljasta_koordinaatid() -> None: pass
......IMPLEMENTS
use strict

interface PointMathFuncs:
def get_point_x_cord() -> float: pass
def get_point_y_cord() -> float: pass

class Line implements PointMathFuncs:
def **init**(self,x:float,y:float) -> None:
self.x: float = x
self.y: float = y
def get_point_x_cord() -> float:
return x
def get_point_y_cord() -> float:
return y

...ENUM
On lisatud võtmesõna: enum kahe konstruuktoriga

use strict

enum ex1:
one :int,
two :int

enum ex:
one : int = 3,
two : int = 4

Enum standartselt itereritatakse väärtusi järgi. Võimalik itereerida nagu "võtti" - "väärtusi"

for element in ex1:
print(str(element.name) + ": " + str(element.value))

TYPE ALIAS
Laseb defineerida oma andmestruktuurid objekti baasil

type my_int_type = int

OPTIONAL
optional muutujade süsteem kasutades keytäht "?". Kasutatakse muutujade defineerimiseks kus ei pea olema väärtust

PRIVAATSUS
privaatsuse piirkonnad kasutades võtmesõnad - public, prrotected, private. Saama reeglidega mis kasutatakse Javas või C-taolised P. keeled.

Kus pärast defineerimist, väljadele juurdepääseks kasutatakse reeglid:
private: pärast defineerimist, võimalik muutujad kutsuda kasutades "\__" muutuja nime enne
protected: pärast defineerimist, võimalik muutujad kutsuda kasutades "_" muutuja nime enne
public: pärast defineerimist, kutsumine toimub standartse viisil
