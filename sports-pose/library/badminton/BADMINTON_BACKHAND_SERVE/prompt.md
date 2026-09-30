# BADMINTON_BACKHAND_SERVE

Right-handed badminton low backhand serve (doubles): right foot forward, racket in front of the waist, shuttle held by the feathers and struck on the cork well below 1.15 m.

- 이름(ko): 배드민턴 백핸드 서브, 숏 서브, 로우 서브, 복식 서브
- names (en): badminton backhand serve, low short serve, doubles serve, backhand low serve

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BADMINTON_BACKHAND_SERVE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 40 deg, turned 14 deg to the athlete's left of the chest line; face pointing down and slightly forward. Eyes on the shuttle.
- Torso: trunk line (hips to shoulders) 20 deg forward of vertical; spine flexed 8 deg over the pelvis; shoulders square with the hips.
- Right arm (racket arm): upper arm raised 40 deg from the side of the trunk, pointing down and slightly forward; elbow bent to about a right angle (95 deg flexion); forearm pointing forward and slightly to the athlete's left and slightly up; palm facing down and slightly to the athlete's left; wrist flexed 10 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.26 m above the floor.
- Left arm (holds the shuttle by the feathers): upper arm raised 8 deg from the side of the trunk, pointing down; elbow bent (63 deg flexion); forearm pointing forward and down; palm facing up and backward and slightly to the athlete's right; wrist flexed 70 deg; hand: cupped, fingers slightly curled and spread; fingertips 0.90 m above the floor.
- Right leg (front foot): hip flexed 25 deg; knee slightly bent (25 deg flexion); thigh pointing down, shin pointing down; ankle dorsiflexed 11 deg; foot flat on the floor.
- Left leg: hip flexed 5 deg; knee slightly bent (20 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle neutral; on the ball of the foot, heel raised.
- Base: ankles 46 cm apart (26% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- Technique cue: hold the shuttle by the feathers, cork facing the racket
- Technique cue: push with the thumb and fingers, short swing
- Technique cue: flat path just over the tape

3. OBJECT_INTERACTION:
- racket (66 cm long): gripped in the right hand, shaft pointing backward and down and slightly to the athlete's left, string face turned backward and up; head centre 0.91 m above the floor; strings and frame clearly visible, one racket only.
- shuttle: feathered shuttlecock, cork leading, flying forward, 0.93 m above the floor.
- Legal under the BWF rules: the whole shuttle is below 1.15 m when struck; both of the server's feet are on the court; the racket meets the cork first.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the net.
- wide_cinema: high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, green court and lines, arena lights.

5. KINETIC_ENERGY:
- shuttle just leaving the strings
- quiet, controlled stillness of the body
- focused expression
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed badminton player hitting a low backhand serve in doubles. Right foot forward near the short service line, knees slightly bent, weight forward; racket held in front of the waist with a backhand grip, head pointing down and to the left, face toward the net; left hand holding the shuttle by the tips of the feathers in front of the strings, cork toward the racket. Hold the shuttle by the feathers, cork facing the racket. Push with the thumb and fingers, short swing. Flat path just over the tape. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, racket strings and shuttle sharp. Shuttle just leaving the strings; quiet, controlled stillness of the body. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, racket head merged into the hand, shuttle flying feathers first, left-handed player, shuttle held by the cork, contact above the waist, server's foot lifted, serve struck above the waist, server lifting a foot, racket hitting the feathers, shuttle resting on the strings
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
| z:shuttle | 0.9 | ..1.1 | the whole shuttle must be below 1.15 m when struck (its top is about 4 cm above its centre) | BWF |
| r_foot_z | 0.0 | ..0.03 | both feet in contact with the court, stationary | BWF |
| l_foot_z | 0.0 | ..0.03 | both feet in contact with the court, stationary | BWF |

## Official game rules (BWF Laws of Badminton V5.0 (in force 26 April 2025; new Laws with 3x15 scoring from 4 January 2027, Law 9 unchanged per secondary sources))

| rule | what | check on this skeleton |
|---|---|---|
| BWF 9.1.6 | Service height: At the instant of being hit by the server's racket the whole shuttle must be below 1.15 m from the court surface. | OK: top of the shuttle 0.97 m (limit 1.15 m) |
| BWF 9.1.4 | Server's feet: Some part of both feet of the server and receiver must remain in contact with the court in a stationary position until the service is delivered. | OK: feet on the floor |
| BWF 9.1.5 | Base of the shuttle first: The server's racket must initially hit the base (cork) of the shuttle. | text only |
| BWF 13.3.7 | Sling or double hit: The shuttle may not be caught and held on the racket and then slung, nor hit twice in succession by the same player. | text only |
| equipment | racket_length | OK: length_m 0.665 (official 0.5-0.68, BWF 4 (at most 680 mm)) |

Scene rules for a full match shot (players, uniforms, officials):

- Court 13.40 x 6.10 m with 40 mm white or yellow lines; net 1.524 m high at the centre and 1.55 m at the posts, dark mesh with a 75 mm white top tape. (BWF 1)
- Umpire on a high chair at one end of the net, service judge on a low chair at the opposite post, line judges behind or beside their lines; with the fixed-height rule a 1.15 m service-height device stands by the court. (BWF 17)
- Feathered shuttlecock with 16 white feathers and a cork base; one racket per player, strings in a crossed pattern. (BWF 2, 4)

Rulebook: https://extranet.bwf.sport/docs/document-system/81/1466/1470/Section%204.1%20-%20Laws%20of%20Badminton%20-%2026%20April%202025%20V5.0%20(2)%20.pdf

## Sources

- [BWF] BWF Laws of Badminton V5.0 (26 April 2025), Law 9 service https://extranet.bwf.sport/docs/document-system/81/1466/1470/Section%204.1%20-%20Laws%20of%20Badminton%20-%2026%20April%202025%20V5.0%20(2)%20.pdf
- [EST] Estimate from coaching descriptions (no measured value found this session) 
