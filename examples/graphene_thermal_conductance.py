from md import *
from phbath import *
from ebath import *
from lammpsdriver import *
from matrix import *
from myio import *
from postprocessing import *

lammpsinfile = [
#    "log none",
    "units metal ",
    "dimension 3 ",
    "boundary p p p",
    "atom_style full",
    "read_data graphene.data ",
    "pair_style rebo ",
    "pair_coeff * * CH.rebo C",
    "min_style cg",
    "minimize 1e-25 1e-25 5000 10000",
]
# -------------------------------------------------------------------------------------
# temperature
T = 300
delta = 0.1
nrep = 2
# time = 0.658fs #time unit
dt = 0.25/0.658
# number of md steps
nmd = 2**10
# transiesta run dir,
# where to find default settings, and relaxed structure *.XV
# SDir="../CGrun/"
# -------------------------------------------------------------------------------------

# initialise lammps run
lmp = lammpsdriver(infile=lammpsinfile)
#
#print lmp.els
# forces...
# q is 1d array made from
# the displacement from equilibrium in unit of lmp.conv * 0.06466 Ang.,
# which is the internal unit of md
q = N.zeros(len(lmp.xyz))
#print q
lmp.force(q)

print("initialise md")
fixatoms = list(range(0*3, (7+1)*3))
fixatoms.extend(list(range(88*3, (95+1)*3)))

# print(("constraint:",constraint))
# Molecular Junction atom indices
slist = list(range(24, 71+1))
# atom indices that are connecting to debyge bath
ecatsl = list(range(8, 23+1))
ecatsr = list(range(72, 87+1))

dynamicatoms = slist+ecatsl+ecatsr
dynamicatoms.sort()
print("the following atoms are dynamic:\n")
print(dynamicatoms)
print(len(dynamicatoms))

# if slist is not given, md will initialize it using xyz
mdrun = md(dt, nmd, T, syslist=None, axyz=lmp.axyz, writepq=True,
           nrep=nrep, npie=1, constr=fixatoms, nstep=100)
# attache lammps driver to md
mdrun.AddLMPint(lmp)
# --------------------------------------------------------------------------------------
# unit in 0.658211814201041 fs
damp = 100/0.658211814201041
ndl = len(ecatsl)
ndr = len(ecatsr)
etal = (1.0/damp)*N.identity(3*ndl, N.float)
etar = (1.0/damp)*N.identity(3*ndr, N.float)
# --------------------------------------------------------------------------------------

# -----------------------------------------------------------------------
# atom indices that are connecting to bath
ebl = ebath(ecatsl, T*(1+delta), mdrun.dt, mdrun.nmd,
            wmax=1., nw=500, bias=0.0, efric=etal, zpmotion=False)
mdrun.AddBath(ebl)

ebr = ebath(ecatsr, T*(1-delta), mdrun.dt, mdrun.nmd,
            wmax=1., nw=500, bias=0.0, efric=etar, zpmotion=False)
mdrun.AddBath(ebr)
# ----------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# MD
# ------------------------------------------------------------------------------
mdrun.Run()
# ------------------------------------------------------------------------------
# close lammps instant
lmp.quit()
CTC(delta=delta, temp=T, dlist=list(range(1)))
# ----------------
