# TAEKWONDO_FIGHTING_STANCE

Taekwondo sparring stance (closed stance, left foot forward): side-on, feet a long step apart on the balls of the feet, knees soft, fists low in front of the trunk, chin down.

- 이름(ko): 태권도 겨루기 준비 자세, 태권도 스탠스, 겨루기 자세, 태권도 가드
- names (en): taekwondo fighting stance, sparring stance, gyeorugi stance, taekwondo guard

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TAEKWONDO_FIGHTING_STANCE

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 28 deg to the athlete's left of the chest line; face pointing forward and slightly to the athlete's left. Eyes on the opponent over the lead shoulder.
- Torso: trunk line (hips to shoulders) 10 deg forward of vertical; spine flexed 5 deg over the pelvis; shoulders square with the hips.
- Right arm (rear arm guard): upper arm raised 25 deg from the side of the trunk, pointing down and slightly forward; elbow fully folded (115 deg flexion); forearm pointing forward and up and slightly to the athlete's left; palm facing to the athlete's left and slightly down; wrist neutral; hand: closed fist; fingertips 1.43 m above the floor.
- Left arm (lead arm guard): upper arm raised 35 deg from the side of the trunk, pointing down and slightly forward; elbow bent to about a right angle (95 deg flexion); forearm pointing forward and slightly up; palm facing to the athlete's right and slightly down and slightly forward; wrist neutral; hand: closed fist; fingertips 1.40 m above the floor.
- Right leg (rear leg): hip extended 10 deg; knee slightly bent (12 deg flexion); thigh pointing down and slightly backward, shin pointing down and slightly backward; ankle neutral; on the ball of the foot, heel raised.
- Left leg (front leg): hip flexed 25 deg; knee slightly bent (20 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle plantar-flexed (toes pointed) 12 deg; foot flat on the floor.
- Base: ankles 53 cm apart (29% of body height, 1.3x shoulder width); every support foot touches the floor, none floats.
- Technique cue: bounce lightly on the balls of the feet
- Technique cue: hands low enough to block kicks to the trunk
- Technique cue: keep the rear heel off the mat to kick instantly

3. OBJECT_INTERACTION:
- Opponent about 2 m away, just out of kicking range.
- Legal under the WT rules: neither fist is on the opponent's face.

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, fists low, eyes over the lead shoulder.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: long stance on the balls of the feet.
- low_cinema: camera 0.6 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame on the mat, arena lights.

5. KINETIC_ENERGY:
- light bounce in the knees
- white dobok creasing at the belt
- sensor socks and trunk protector visible
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a taekwondo athlete in a sparring stance. Left foot forward and right foot back a long step apart, both heels slightly raised on the balls of the feet, knees soft; body side-on to the opponent; fists loosely closed in front of the trunk at chest height, lead forearm angled across the body, rear fist near the solar plexus; chin down. Bounce lightly on the balls of the feet. Hands low enough to block kicks to the trunk. Keep the rear heel off the mat to kick instantly. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, fists low, eyes over the lead shoulder. Light bounce in the knees; white dobok creasing at the belt. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, black belt missing, trunk protector missing, kicking with the shin instead of the foot, bare chest, boxing gloves, southpaw stance, punch to the opponent's face, hand grabbing the opponent's dobok, catching the opponent's kicking leg, knee strike, head butt, athlete standing outside the contest area line
```

## Control images

- `openpose_front.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.6 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| stance_over_shoulders | 1.3 | 1.2..2.4 | a long side-on stance, feet a long step apart | KUK, EST |
| r_knee_flex | 12.2 | 8..40 | knees soft, bouncing on the balls of the feet | EST |
| l_elbow_flex | 95.0 | 70.. | lead fist in front of the trunk, elbow bent | EST |

## Official game rules (World Taekwondo Competition Rules & Interpretation (Olympic sparring, kyorugi))

| rule | what | check on this skeleton |
|---|---|---|
| WT Prohibited acts (gam-jeom): hitting the head with the hand | Hand attack to the face: Hitting the opponent's head or face with the hand is a gam-jeom; the head may be attacked only by kicks. | not measurable here ("unknown point 'B.nose'") |
| WT Prohibited acts (gam-jeom): grabbing, holding, pushing | Grabbing or pushing: Grabbing or holding the opponent or the opponent's leg or dobok, and pushing the opponent with the hands or body, are gam-jeom. | text only |
| WT Prohibited acts (gam-jeom): knee and head attacks | Kneeing or head butting: Attacking with the knee or butting with the head is a gam-jeom. | text only |
| WT Prohibited acts (gam-jeom): crossing the boundary line | Stepping out of the contest area: Stepping out over the boundary line of the contest area is a gam-jeom, and so is falling down. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- White dobok with a belt; electronic trunk protector and headgear in the athlete's colour, red (hong) or blue (chung); forearm and shin guards, gloves, sensor socks, groin guard and mouthguard, all worn under or over the dobok as the rules require. (WT Uniform and protective equipment)
- Flat, non-slip mat; the contest area is marked as an octagon (Olympic events) or a square, with a boundary line. (WT Competition area)
- One referee on the mat in a uniform; judges and a video-replay jury off the mat; coaches seated at the corners. (WT Officials)
- Punches with the knuckles of a tightly clenched fist, only to the trunk protector; kicks with the foot below the ankle bone, to the trunk protector or to the head above the collar bone. (WT Permitted techniques)

Rulebook: https://www.worldtaekwondo.org/rules-wt/rules.html

## Sources

- [KUK] Kukkiwon Taekwondo Textbook: fighting stance (gyeorugi junbi), dollyeo chagi and dwit chagi descriptions - general knowledge, not re-checked this session https://www.kukkiwon.or.kr
- [EST] Estimate from standard taekwondo coaching (no measured joint angle checked this session) 
