#!/usr/bin/python
# -*- coding: UTF-8 -*- 
import os
import subprocess
import sys

import numpy as N
from lammps import lammps
from sgdml.predict import GDMLPredict
from sgdml.train import GDMLTrain
from sgdml.utils import io
from tqdm import tqdm

from lammpsdriver import get_atomname
from units import AtomicMassTable, PeriodicTable

args = "-screen none"

lammpsinfile=[
"units metal ",
"dimension 3 ",
"boundary p p p",
"atom_style full",
"read_data test.data",
"pair_style rebo ",
"pair_coeff * * CH.airebo C",
"fix 1 all nve",
#"dump 1 all xyz 1000 dump*.xyz",
"run 0"
]

lmp = lammps(cmdargs=args.split())
lmp.commands_list(lammpsinfile)

natoms = lmp.get_natoms()
atomtype = N.array(lmp.gather_atoms("type", 0, 1))
mass= lmp.extract_atom("mass",2)
els=[]
for i in range(natoms):
        els.append(get_atomname(mass[atomtype[i]]))

nstep=4*10**5
nwrite=1

with open("trajectories.xyz", 'w') as trajfile:
        xyz=N.array(lmp.gather_atoms("x",1,3))
        force=N.array(lmp.gather_atoms("f",1,3))
        trajfile.write(str(natoms)+'\n'+str(lmp.get_thermo("etotal"))+'\n')
        for ip in range(natoms):
                trajfile.write(str(els[ip])+'    '+str(xyz[ip*3])+'   '+str(xyz[ip*3+1])+'   '+str(xyz[ip*3+2])+'   '+str(force[ip*3])+'   '+str(force[ip*3+1])+'   '+str(force[ip*3+2])+'\n')
        for i in tqdm(range(nstep),unit="steps"):
                lmp.command("run 1")
                if i % nwrite == 0:
                        xyz=N.array(lmp.gather_atoms("x",1,3))
                        force=N.array(lmp.gather_atoms("f",1,3))
                        trajfile.write(str(natoms)+'\n'+str(lmp.get_thermo("etotal"))+'\n')
                        for ip in range(natoms):
                            trajfile.write(str(els[ip])+'    '+str(xyz[ip*3])+'   '+str(xyz[ip*3+1])+'   '+str(xyz[ip*3+2])+'   '+str(force[ip*3])+'   '+str(force[ip*3+1])+'   '+str(force[ip*3+2])+'\n')

lmp.close()

#This module contains all routines for training GDML and sGDML models.
#extendxyz=open("trajectories.xyz","r")
#subprocess.call(["cat trajectories*ani > trajectories.xyz"],shell=True)
if os.path.exists("trajectories.npz"):
    os.remove("trajectories.npz")
subprocess.call(["sgdml_dataset_from_xyz.py trajectories.xyz"],shell=True)
#Force field reconstruction
dataset = N.load("trajectories.npz")
n_train = 200

gdml_train = GDMLTrain()
task = gdml_train.create_task(dataset, n_train,\
        valid_dataset=dataset, n_valid=1000,\
        sig=10, lam=1e-15)

try:
        model = gdml_train.train(task)
except Exception, err:
        sys.exit(err)
else:
        N.savez_compressed('FFftraj.npz', **model)
        
#Force field query
#model = N.load('FFftraj.npz')
gdml = GDMLPredict(model)

r,_ = io.read_xyz('target.xyz') 
e,f = gdml.predict(r)

print r.shape 
print e.shape 
print f.shape 