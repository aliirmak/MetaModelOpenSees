# 2D Elastic Structure Static
# Analysis Name: Use of 2d Elastic Beam Column Element
# Analysis Description: Simple Introduction to OpenSees
# Analysis Type: Distributed Load & Pushover Analysis
#--------
# Author: aio
# Unit System: kips, in, sec
# Date: November 23, 2018

#--------
# Set constants
# This is tcl code but defined in OpenSees domain
set Load1 [expr 1185.0]
set Load2 [expr 1185.0]
set Load3 [expr 970]
set PI [expr 2.0 * asin(1.0)]
set ft [expr 12.0]
set g [expr 386.4]
set m1 [expr $Load1/(4*$g)]; # 4 nodes per floor
set m2 [expr $Load1/(4*$g)]
set m3 [expr $Load1/(4*$g)]
set w1 [expr $Load1/(90*$ft)]; # frame 90 ft long
set w2 [expr $Load2/(90*$ft)]
set w3 [expr $Load3/(90*$ft)]

#--------
# Set ModelBuilder
model BasicBuilder -ndm 2 -ndf 3; # two-dimensions and 3 DOF/node

#--------
# Create nodes & add to Domain
# command: node nodeId xCrd yCrd <-mass $massX $massY $massRz>
# NOTE: mass in optional
node 1 0.0 0.0
node 2 360.0 0.0
node 3 720.0 0.0
node 4 1080.0 0.0
node 5 0.0 162.0 -mass $m1 $m1 0.0
node 6 360.0 162.0 -mass $m1 $m1 0.0
node 7 720.0 162.0 -mass $m1 $m1 0.0
node 8 1080.0 162.0 -mass $m1 $m1 0.0
node 9 0.0 324.0 -mass $m2 $m2 0.0
node 10 360.0 324.0 -mass $m2 $m2 0.0
node 11 720.0 324.0 -mass $m2 $m2 0.0
node 12 1080.0 324.0 -mass $m2 $m2 0.0
node 13 0.0 486.0 -mass $m3 $m3 0.0
node 14 360.0 486.0 -mass $m3 $m3 0.0
node 15 720.0 486.0 -mass $m3 $m3 0.0
node 16 1080.0 486.0 -mass $m3 $m3 0.0

#--------
# Set the boundary conditions - command
# command: fix nodeID xResrnt? yRestrnt? rZRestrnt?
fix 1 1 1 1
fix 2 1 1 1
fix 3 1 1 1
fix 4 1 1 1

#--------
# Define geometric transformations
geomTransf Linear 1; # beams
geomTransf PDelta 2; # columns

#--------
# Define elements
element elasticBeamColumn 1 1 5 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 2 5 9 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 3 9 13 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 4 2 6 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 5 6 10 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 6 10 14 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 7 3 7 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 8 7 11 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 9 11 15 91.4 29000.0 4330.0 2; # W14X311
element elasticBeamColumn 10 4 8 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 11 8 12 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 12 12 16 75.6 29000.0 3400.0 2; # W14X257
element elasticBeamColumn 13 5 6 34.7 29000.0 5900.0 1; # W33X118
element elasticBeamColumn 14 6 7 34.7 29000.0 5900.0 1; # W33X118
element elasticBeamColumn 15 7 8 34.7 29000.0 5900.0 1; # W33X118
element elasticBeamColumn 16 9 10 34.2 29000.0 4930.0 1; # W30X116
element elasticBeamColumn 17 10 11 34.2 29000.0 4930.0 1; # W30X116
element elasticBeamColumn 18 11 12 34.2 29000.0 4930.0 1; # W30X116
element elasticBeamColumn 19 13 14 20.1 29000.0 1830.0 1; # W24X68
element elasticBeamColumn 20 14 15 20.1 29000.0 1830.0 1; # W24X68
element elasticBeamColumn 21 15 16 20.1 29000.0 1830.0 1; # W24X68

#--------
# Define analysis
# static analysis for gravity loads
timeSeries Linear 1; # create a Linear TimeSeries

# Create a Plain load pattern with a linear TimeSeries
pattern Plain 1 1 {
    eleLoad -ele 13 14 15 -type -beamUniform -$w1
    eleLoad -ele 16 17 18 -type -beamUniform -$w2
    eleLoad -ele 19 20 21 -type -beamUniform -$w3
}

#--------
# Define analysis solver settings
system BandSPD; # Create the system of equation, a SPD using a band storage scheme
numberer RCM; # Create the DOF numberer, the reverse Cuthill-McKee algorithm
constraints Plain; # Create the constraint handler, a Plain handler is used as homo constraints
integrator LoadControl 1; # Create the integration scheme, the LoadControl scheme using steps of 1.0
test NormDispIncr 1.0e-10 6; # Create the solution algorithm, a Linear algorithm is created
algorithm Newton
analysis Static


analyze [expr 1]


# lateral load analysis
loadConst -time 0.0; # set gravity loads constant and time in domain to be t = 0.0

timeSeries Linear 2; # create a Linear TimeSeries

# Create a Plain load pattern with a linear TimeSeries
pattern Plain 2 2 {
    load 9 180.0 0.0 0.0
    load 13 220.0 0.0 0.0
    load 5 90.0 0.0 0.0
}

#--------
# Define analysis solver settings
system BandSPD; # Create the system of equation, a SPD using a band storage scheme
numberer RCM; # Create the DOF numberer, the reverse Cuthill-McKee algorithm
constraints Plain; # Create the constraint handler, a Plain handler is used as homo constraints
integrator LoadControl 1; # Create the integration scheme, the LoadControl scheme using steps of 1.0
test NormDispIncr 1.0e-10 6; # Create the solution algorithm, a Linear algorithm is created
algorithm Newton
analysis Static

recorder Element -file EleForces.out -ele 1 4 7 10 forces
recorder Node -xml NodeDisp.out -time -nodeRange 5 16 -dof 1 disp

analyze [expr 10]


