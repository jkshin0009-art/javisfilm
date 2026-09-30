# BADMINTON_NET_LUNGE

Right-handed badminton forehand lunge to the net: long step with the right foot landing heel first, front knee over the ankle, rear leg extended, racket reaching forward with the face nearly level.

- 이름(ko): 배드민턴 네트 런지, 헤어핀 런지, 네트 앞 런지, 배드민턴 네트샷
- names (en): badminton net lunge, forehand net shot lunge, hairpin lunge, lunge to the net

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BADMINTON_NET_LUNGE

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward and slightly down. Eyes on the shuttle just above the net tape.
- Torso: trunk line (hips to shoulders) 20 deg forward of vertical; spine flexed 5 deg over the pelvis; shoulders square with the hips.
- Right arm (racket arm reaching to the net): upper arm raised 75 deg from the side of the trunk, pointing forward and down; elbow slightly bent (15 deg flexion); forearm pointing forward and slightly down; palm facing down and to the athlete's left and slightly forward; wrist extended (cocked back) 25 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.76 m above the floor.
- Left arm (balance arm): upper arm raised 50 deg from the side of the trunk, pointing backward and slightly to the athlete's left and slightly down; elbow slightly bent (20 deg flexion); forearm pointing down and slightly to the athlete's left and slightly backward; palm facing to the athlete's right and slightly down and slightly backward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 0.64 m above the floor.
- Right leg (lunging leg): hip flexed 95 deg; knee bent to about a right angle (78 deg flexion); thigh pointing forward, shin pointing down; ankle dorsiflexed 12 deg; heel down, toes raised.
- Left leg (trailing leg): hip extended 35 deg; knee slightly bent (28 deg flexion); thigh pointing backward and down, shin pointing backward; ankle dorsiflexed 19 deg; on the ball of the foot, heel raised.
- Base: ankles 121 cm apart (68% of body height, 3.0x shoulder width); every support foot touches the floor, none floats.
- Technique cue: lunge with the racket foot, toe to the net corner
- Technique cue: racket arm extended, face nearly parallel to the floor
- Technique cue: hit and land at the same moment

3. OBJECT_INTERACTION:
- racket (66 cm long): gripped in the right hand, shaft pointing forward and slightly up, string face turned down and to the athlete's left and slightly forward; head centre 0.93 m above the floor; strings and frame clearly visible, one racket only.
- shuttle: feathered shuttlecock, cork leading, flying forward and slightly up, 0.98 m above the floor.
- Net 1.524 m high, 160 cm in front; the racket stays on the player's side of the net.
- Legal under the BWF rules: no contact with the net; shuttle and racket are on the player's own side of the net.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the net.
- wide_cinema: high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, green court and lines, arena lights.

5. KINETIC_ENERGY:
- shoe squeaking on the court, slight slide of the front heel
- shuttle just above the tape
- sweat on the forearm
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed badminton player lunging to the net to play a forehand net shot. Long lunge with the right foot, heel landing first and toes pointing at the net, right knee bent about 90 degrees directly over the ankle; left leg extended behind on the ball of the foot; trunk upright; right arm reaching forward, racket in front with the face nearly level under the shuttle; left arm back for balance. Lunge with the racket foot, toe to the net corner. Racket arm extended, face nearly parallel to the floor. Hit and land at the same moment. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp. Shoe squeaking on the court, slight slide of the front heel; shuttle just above the tape. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, racket head merged into the hand, shuttle flying feathers first, left-handed player, left foot forward on a forehand lunge, front knee collapsing inward, trunk folded over the knee, racket touching the net, racket reaching over the net, shuttle resting on the strings
```

## Control images

- `openpose_net_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: l_leg.flex = -35 is beyond the usual range -30..125

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| stride_pct_height | 68.1 | 55..85 | long lunge step (maximum about 1.47 m in men) | PLOS18 |
| r_knee_flex | 78.0 | 75..105 | front knee bent about 90 deg over the ankle | EST |
| l_knee_flex | 28.5 | ..35 | trailing leg extended | EST |
| trunk_lean_fwd | 20.0 | ..30 | trunk upright, not folded over the knee | EST |

## Official game rules (BWF Laws of Badminton V5.0 (in force 26 April 2025; new Laws with 3x15 scoring from 4 January 2027, Law 9 unchanged per secondary sources))

| rule | what | check on this skeleton |
|---|---|---|
| BWF 13.4.1 | Touching the net: It is a fault if a player touches the net or its supports with the racket, person or dress while the shuttle is in play. | OK: closest body part to the net: r hand, 79 cm |
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

- [PLOS18] Badminton lunge: maximum lunge 1.47 m (men), 1.16 m (women); heel-first landing (search extract) https://pmc.ncbi.nlm.nih.gov/articles/PMC6185854
- [EST] Estimate from coaching descriptions (no measured value found this session) 
