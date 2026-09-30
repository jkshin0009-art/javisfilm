# SOCCER_INSTEP_KICK_CONTACT

Right-footed soccer instep kick at ball contact: laces strike the ball centre, toes pointed and ankle locked, support knee bent, body over the ball.

- 이름(ko): 축구 인스텝 킥 임팩트, 슈팅 순간, 발등 슛, 강슛 임팩트
- names (en): soccer instep kick contact, shot impact, laces strike, power shot contact

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SOCCER_INSTEP_KICK_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 60 deg; face pointing down and slightly forward and slightly to the athlete's right. Head down over the ball, eyes on the contact point.
- Torso: trunk line (hips to shoulders) 12 deg forward of vertical, leaning 16 deg to the athlete's left; spine flexed 14 deg over the pelvis; shoulders square with the hips.
- Right arm (swings across the body): upper arm raised 40 deg from the side of the trunk, pointing down and slightly forward; elbow bent (60 deg flexion); forearm pointing forward and slightly to the athlete's left; palm facing to the athlete's left and down and slightly backward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.10 m above the floor.
- Left arm (balance arm, out wide): upper arm raised 80 deg from the side of the trunk, pointing to the athlete's left and slightly down; elbow slightly bent (25 deg flexion); forearm pointing to the athlete's left and slightly down; palm facing backward and slightly down; wrist neutral; hand: open with fingers spread; fingertips 0.98 m above the floor.
- Right leg (kicking leg): hip flexed 27 deg; knee deeply bent (68 deg flexion); thigh pointing down and slightly forward, shin pointing down and backward and slightly to the athlete's right; ankle plantar-flexed (toes pointed) 55 deg; on the ball of the foot, heel raised.
- Left leg (support leg): hip flexed 16 deg; knee bent (42 deg flexion); thigh pointing down and slightly forward, shin pointing down and slightly backward; ankle dorsiflexed 25 deg; foot flat on the floor.
- Base: ankles 29 cm apart (16% of body height, 0.7x shoulder width); every support foot touches the floor, none floats.
- Technique cue: toe pointed down and ankle locked
- Technique cue: strike through the centre of the ball with the laces
- Technique cue: hips square to the target at contact
- Technique cue: knee over the ball keeps the shot low

3. OBJECT_INTERACTION:
- ball (22 cm diameter): center 0.11 m above the floor; touching the right instep; surface 20 cm from the left ankle (to the athlete's right and slightly forward of it).

4. CINEMATIC_CAMERA:
- side_low: camera 0.3 m above the floor, ground-level low angle looking up, side profile view, 35mm standard lens, full-body shot. Ground-level side view, laces meeting the ball, ball slightly deformed at impact.
- goal_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Goalkeeper's point of view, compressed telephoto perspective, sharp focus on the ball.
- wide_cinema: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Wide low frame, stadium lights and crowd blurred behind.

5. KINETIC_ENERGY:
- ball compressing against the laces, first frame of flight
- grass spray and a small divot flying off the turf
- motion blur on the kicking shin, support leg sharp
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a soccer player striking a right-footed instep shot, the laces hitting the centre of the ball. Left support foot planted flat beside the ball, left knee bent about 40 degrees; right kicking leg swinging through with the knee still slightly bent, ankle locked and toes pointed down, the top of the foot (laces) meeting the back centre of the ball; hips turned square to the goal; trunk over the ball; left arm out wide, right arm swinging across. Toe pointed down and ankle locked. Strike through the centre of the ball with the laces. Hips square to the target at contact. Knee over the ball keeps the shot low. Camera 0.3 m above the floor, ground-level low angle looking up, side profile view, 35mm standard lens, full-body shot. Ground-level side view, laces meeting the ball, ball slightly deformed at impact. Ball compressing against the laces, first frame of flight; grass spray and a small divot flying off the turf. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, foot passing through the ball, toe pointed up (toe poke), ball larger than the foot, support foot hovering, kicking-side arm thrown forward, knee bent backwards
```

## Control images

- `openpose_side_low.png` / `.json`: 1152x896, camera 0.3 m above the floor, ground-level low angle looking up, side profile view, 35mm standard lens, full-body shot.
- `openpose_goal_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: head.flex = 60 is beyond the usual range -65..56

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_thigh_fwd | 29.2 | 15..50 | kicking thigh swinging forward, knee over or just behind the ball (hip reported near neutral, -7 to 15 deg, against a tilted pelvis frame) | S2 |
| r_knee_flex | 68.0 | 30..70 | kicking knee still bent and extending at impact (about 43-67 deg) | S2, S4 |
| r_leg.ankle | 55.2 | 50.. | ankle plantar-flexed and locked, toes pointed down | S1 |
| l_knee_flex | 42.0 | 30..55 | support knee about 42 deg flexion at contact | S3 |
| l_foot_z | 0.0 | ..0.03 | support foot planted | S3 |
| trunk_lean_fwd | 12.4 | -5..20 | body over the ball, not leaning far back | S5 |

## Sources

- [S1] Kellis & Katis 2007, JSSM 6:154: at impact the hip is flexed, the knee extending, the ankle plantar-flexed https://www.jssm.org/hf.php?id=jssm-06-154.xml
- [S2] Systematic review of instep-kick kinematics in elite adult players (hip -7 to 15 deg, knee 67 +/- 19 deg at impact) https://drantoniopetrolo.ca/wp-content/uploads/2024/01/KINEMATIC-DETERMINANTS-OF-THE-INSTEP-SOCCER-KICK-IN-ELITE-ADULT-SOCCER-PLAYERS_A-SYSTEMATIC-REVIEW.pdf
- [S3] Lees et al. 2010, J Sports Sci review: support knee 42 deg at contact https://pubmed.ncbi.nlm.nih.gov/20509089/
- [S4] Kapidzic et al. 2014: swinging-leg knee 136.5 deg included angle (about 43.5 deg flexion) https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4234773/
- [S5] Nunome et al. 2002/2006: instep ball speed about 28 m/s, contact under 10 ms https://pubmed.ncbi.nlm.nih.gov/16368610/
