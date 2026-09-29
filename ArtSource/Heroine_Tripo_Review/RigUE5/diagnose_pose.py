exec(open(__file__.replace('diagnose_pose.py','test_poses.py')).read().split('poses=sys.argv')[0])
pose('squat')
for n in ['ORG-thigh.L','ORG-thigh.R','skirt_00.01','MCH-garment_follow_00','torso']:
 p=rig.pose.bones[n];print(n,list(p.head),list(p.matrix_basis.to_euler()),list(p.matrix.to_euler()))
