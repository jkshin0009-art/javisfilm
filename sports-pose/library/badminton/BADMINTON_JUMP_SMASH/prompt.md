# BADMINTON_JUMP_SMASH

Right-handed badminton jump smash at contact: airborne with a scissor kick, racket arm reaching up in front of the hitting shoulder, forearm pronating, left arm pulled down, shuttle hit high in front.

- 이름(ko): 배드민턴 점프 스매시, 스매시 타점, 점프 스매싱, 배드민턴 공격
- names (en): badminton jump smash, smash contact, jumping smash, overhead smash

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BADMINTON_JUMP_SMASH

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 52 deg, turned 11 deg to the athlete's right of the chest line; face pointing forward and up. Eyes on the shuttle.
- Torso: trunk line (hips to shoulders) 13 deg forward of vertical, leaning 12 deg to the athlete's left; spine flexed 8 deg over the pelvis; shoulder line rotated 20 deg to the left of the hip line (hip-shoulder separation).
- Right arm (racket arm): upper arm raised 160 deg from the side of the trunk, pointing up and slightly forward; elbow slightly bent (22 deg flexion); forearm pointing up; palm facing forward and slightly down; wrist flexed 10 deg; hand: fingers wrapped firmly around what it holds; fingertips 2.47 m above the floor.
- Left arm (non-racket arm, pulled down): upper arm raised 45 deg from the side of the trunk, pointing down and slightly forward and slightly to the athlete's right; elbow bent to about a right angle (100 deg flexion); forearm pointing up and forward and slightly to the athlete's right; palm facing to the athlete's right and down; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.76 m above the floor.
- Right leg (scissor kick, forward): hip flexed 50 deg; knee deeply bent (70 deg flexion); thigh pointing forward and down, shin pointing down and slightly backward; ankle plantar-flexed (toes pointed) 30 deg; foot 35 cm above the floor.
- Left leg (scissor kick, back): hip extended 12 deg; knee bent (45 deg flexion); thigh pointing down and slightly backward, shin pointing backward and slightly down; ankle plantar-flexed (toes pointed) 35 deg; foot 43 cm above the floor.
- Airborne: lowest point of the body 35 cm above the floor; neither foot touches the ground.
- Technique cue: contact in front of and above the racket shoulder
- Technique cue: legs switch in the air like scissors
- Technique cue: pull the non-racket arm in as you strike
- Technique cue: land on the non-racket foot first

3. OBJECT_INTERACTION:
- racket (66 cm long): gripped in the right hand, shaft pointing up and slightly forward and slightly to the athlete's left, string face turned forward and slightly down; head centre 2.73 m above the floor; strings and frame clearly visible, one racket only.
- shuttle: feathered shuttlecock, cork leading, flying forward and slightly down, 2.73 m above the floor.
- Net 1.524 m high at the centre, 250 cm in front; the shuttle is struck high on the player's own side.
- Legal under the BWF rules: no contact with the net; shuttle and racket are on the player's own side of the net.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the net.
- wide_cinema: high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, green court and lines, arena lights.

5. KINETIC_ENERGY:
- racket head motion blur, shuttle compressing off the strings
- sweat flying off the hair
- court lights flaring behind the racket
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed badminton player hitting a jump smash at the top of the jump. Airborne with a scissor kick, right knee driven forward and left leg swept back; trunk tilted so the racket shoulder is high; right arm reaching up almost straight in front of the right shoulder, forearm turning over, racket face angled down onto the shuttle; left arm pulled down to the chest. Contact in front of and above the racket shoulder. Legs switch in the air like scissors. Pull the non-racket arm in as you strike. Land on the non-racket foot first. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp. Racket head motion blur, shuttle compressing off the strings; sweat flying off the hair. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, racket head merged into the hand, shuttle flying feathers first, left-handed player, contact behind the head, both legs together in the air, left arm still raised at contact, racket touching the net, racket reaching over the net, shuttle resting on the strings
```

## Control images

- `openpose_net_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 22.0 | 8..40 | racket arm nearly straight but not locked (about 32 deg in a case study; faster smashes with a less extended elbow) | EFS22 |
| r_shoulder_elev | 160.0 | 140..178 | upper arm about 15 deg short of vertical relative to the trunk | ISBS686 |
| z:shuttle | 2.7 | 2.5..3.1 | contact about 2.9 m high in elite men | IJRSS |
| lowest_z | 0.3 | 0.2.. | airborne jump smash | IJRSS |

## Official game rules (BWF Laws of Badminton V5.0 (in force 26 April 2025; new Laws with 3x15 scoring from 4 January 2027, Law 9 unchanged per secondary sources))

| rule | what | check on this skeleton |
|---|---|---|
| BWF 13.4.1 | Touching the net: It is a fault if a player touches the net or its supports with the racket, person or dress while the shuttle is in play. | OK: closest body part to the net: l hand, 194 cm |
| BWF 13.4.2 | Hitting over the net: Invading the opponent's court over the net with racket or person is a fault, except following through after the contact was made on the striker's side. | OK: all on the near side |
| BWF 13.3.7 | Sling or double hit: The shuttle may not be caught and held on the racket and then slung, nor hit twice in succession by the same player. | text only |
| equipment | net_height | OK: height_m 1.524 (official 1.514-1.534, BWF 1 (1.524 m at the centre)) |
| equipment | racket_length | OK: length_m 0.665 (official 0.5-0.68, BWF 4 (at most 680 mm)) |

Scene rules for a full match shot (players, uniforms, officials):

- Court 13.40 x 6.10 m with 40 mm white or yellow lines; net 1.524 m high at the centre and 1.55 m at the posts, dark mesh with a 75 mm white top tape. (BWF 1)
- Umpire on a high chair at one end of the net, service judge on a low chair at the opposite post, line judges behind or beside their lines; with the fixed-height rule a 1.15 m service-height device stands by the court. (BWF 17)
- Feathered shuttlecock with 16 white feathers and a cork base; one racket per player, strings in a crossed pattern. (BWF 2, 4)

Rulebook: https://extranet.bwf.sport/docs/document-system/81/1466/1470/Section%204.1%20-%20Laws%20of%20Badminton%20-%2026%20April%202025%20V5.0%20(2)%20.pdf

## Sources

- [IJRSS] Elite jump smash: contact height 2.90 +/- 0.13 m (men), jump height 53.6 cm (men) - search extract https://revistaseug.ugr.es/index.php/IJRSS/article/view/33248
- [ISBS686] Badminton smash kinematics: arm-to-trunk angle about 164 deg at contact (search extract) https://ojs.ub.uni-konstanz.de/cpa/article/view/686/606
- [EFS22] Smash case study: elbow 148 deg inner angle (about 32 deg flexion) at contact https://efsupit.ro/images/stories/decembrie2022/Art%20404.pdf
- [EST] Estimate from coaching descriptions (no measured value found this session) 
