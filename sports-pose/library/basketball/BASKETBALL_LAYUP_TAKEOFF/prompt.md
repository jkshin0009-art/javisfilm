# BASKETBALL_LAYUP_TAKEOFF

Right-handed basketball layup at takeoff: pushing off the left foot, right knee driven up to hip height, ball carried in both hands up past the right shoulder.

- 이름(ko): 농구 레이업 도약, 레이업 점프, 레이업 슛, 원스텝 레이업
- names (en): basketball layup takeoff, layup jump, right-handed layup, drive to the basket

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASKETBALL_LAYUP_TAKEOFF

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 13 deg; face pointing forward. Eyes on the top corner of the square on the backboard.
- Torso: trunk line (hips to shoulders) 0 deg forward of vertical; shoulder line rotated 10 deg to the left of the hip line (hip-shoulder separation).
- Right arm (shooting hand under the ball): upper arm raised 72 deg from the side of the trunk, pointing forward and slightly down; elbow fully folded (132 deg flexion); forearm pointing up and slightly backward; palm facing up and slightly forward; wrist extended (cocked back) 41 deg; hand: fingers spread around the ball, palm not touching it fully; fingertips 1.86 m above the floor.
- Left arm (guide hand): upper arm raised 108 deg from the side of the trunk, pointing forward and slightly up and slightly to the athlete's right; elbow bent to about a right angle (77 deg flexion); forearm pointing up and to the athlete's right; palm facing to the athlete's right and slightly down; wrist extended (cocked back) 28 deg; hand: fingers spread around the ball, palm not touching it fully; fingertips 2.10 m above the floor.
- Right leg (knee drive (shooting-hand side)): hip flexed 92 deg; knee bent to about a right angle (95 deg flexion); thigh pointing forward, shin pointing down; ankle plantar-flexed (toes pointed) 25 deg; foot 48 cm above the floor.
- Left leg (takeoff leg): hip extended 8 deg; knee slightly bent (10 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle plantar-flexed (toes pointed) 22 deg; on the ball of the foot, heel raised.
- Base: ankles 71 cm apart (38% of body height, 1.7x shoulder width); every support foot touches the floor, none floats.
- Technique cue: right-handed layup: take off from the left foot
- Technique cue: drive the right knee up
- Technique cue: jump up, not out
- Technique cue: protect the ball with two hands up to the shoulder

3. OBJECT_INTERACTION:
- ball (24 cm diameter): center 1.93 m above the floor; surface 25 cm from the right shoulder (up and forward of it).
- Rim 3.05 m high, 150 cm ahead and above; backboard square behind the rim.

4. CINEMATIC_CAMERA:
- baseline_low: low-angle shot looking up, from the front (target side), 35mm standard lens, full-body shot. From under the basket looking up, knee drive and ball carry clear.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: takeoff foot pushing off, thigh horizontal.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide from the wing, defenders blurred, rim in the upper frame.

5. KINETIC_ENERGY:
- sneaker sole flexing on the push-off
- shorts lifted by the knee drive
- motion blur on the trailing arm swing, sharp face
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a basketball player taking off for a right-handed layup. Pushing off the left foot on the ball of the foot, left leg nearly straight; right knee driven up to hip height, thigh horizontal, knee bent about 90 degrees; trunk upright; ball held in both hands and carried up past the right shoulder toward head height, right hand under the ball, left hand on its side. Right-handed layup: take off from the left foot. Drive the right knee up. Jump up, not out. Protect the ball with two hands up to the shoulder. Low-angle shot looking up, from the front (target side), 35mm standard lens, full-body shot. From under the basket looking up, knee drive and ball carry clear. Sneaker sole flexing on the push-off; shorts lifted by the knee drive. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, takeoff from the right foot, both knees driven up, ball held low in one hand, both feet off the floor with no push-off
```

## Control images

- `openpose_baseline_low.png` / `.json`: 896x1152, low-angle shot looking up, from the front (target side), 35mm standard lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_thigh_fwd | 92.0 | 70.. | shooting-side knee driven up, thigh about horizontal | S1, S2 (estimate from technique descriptions) |
| r_knee_flex | 95.0 | 70..110 | swing knee bent about 90 deg | S2 (estimate) |
| l_knee_flex | 10.0 | ..20 | takeoff leg nearly straight at toe-off | S2 (estimate) |
| l_foot_z | 0.0 | ..0.03 | left foot still pushing off the floor (right-handed layup takes off from the left foot) | S1 |
| r_foot_z | 0.5 | 0.3.. | swing foot off the floor | S1 |

## Sources

- [S1] FIBA WABC Level 1 manual 2.7.2: right-handed layup takes off from the left foot, lift the shooting-hand-side knee https://wabc.fiba.com/manual/level-1/l1-player/l1-2-offensive-basketball-skills/2-7-shooting/2-7-2-basic-shooting-teaching-lay-up-footwork/
- [S2] Vint & Hinrichs 1996, J Appl Biomech: one-foot jumps gain height from the free-leg swing https://journals.humankinetics.com/view/journals/jab/12/3/article-p338.xml
