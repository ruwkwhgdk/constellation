import unittest
from test_combat_recipe_v2 import extended
from combat_recipe import validate_recipe
class VFXRecipeTests(unittest.TestCase):
 def test_slots_and_individual_override(self):
  d=extended();d['player']['vfx']={'attack':{'mode':'Builtin','kind':'SwordParry','scale':.5,'color':[1,.2,.1,1]}}
  d['monster_vfx']={'hit':{'mode':'Builtin','kind':'SlimeHit'}}
  d['enemies'][0]['vfx']={'hit':{'mode':'Niagara','system':'/Game/FX/NS_Test','duration':1}}
  self.assertEqual(validate_recipe(d)['enemies'][0]['vfx']['hit']['mode'],'Niagara')
 def test_resolved_inheritance(self):
  d=extended();d['monster_vfx']={'hit':{'mode':'Niagara','system':'/Game/FX/NS_Test'}}
  d['enemies'][0]['vfx']={'hit':{'mode':'Niagara'}}
  self.assertTrue(validate_recipe(d))
  d['enemies'][0]['vfx']={'hit':{'system':None}}
  with self.assertRaisesRegex(ValueError,'system'):validate_recipe(d)
 def test_invalid_slots(self):
  for cue in ({'mode':'Bad'},{'mode':'Niagara'},{'mode':'Builtin','kind':'Bad'},{'scale':0},{'duration':99},{'color':[1,2,3]},{'color':[1,2,float('nan'),1]}):
   d=extended();d['player']['vfx']={'hit':cue}
   with self.assertRaises(ValueError):validate_recipe(d)
if __name__=='__main__':unittest.main()
