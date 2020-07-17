# Naming item templates

In this document we describe a naming convention for the item templates used [here](doc/item_statistics_en.md)
#### Currencies
Most of these are prenamed, but here's an example list:

![](screenshots/item_template_archive/food_1000.png?raw=true) `food_1000`

![](screenshots/item_template_archive/coin.png?raw=true) `coin`

![](screenshots/item_template_archive/coredata.png?raw=true) `coredata`

![](screenshots/item_template_archive/eventpoint_oratorio.png?raw=true) `eventpoint_oratorio`
#### Plates / Boxes / Retrofit BPs
These are pretty self-explanatory:

![](screenshots/item_template_archive/box_T1.png?raw=true) `box_T1`

![](screenshots/item_template_archive/plate_gun_T2.png?raw=true) `plate_gun_T2`

![](screenshots/item_template_archive/retrobp_bb_T3.png?raw=true) `retrobp_bb_T3`
#### Ships
Ships are also pretty self-explanatory.

![](screenshots/item_template_archive/ship_N_cassin.png?raw=true) `ship_N_cassin`

![](screenshots/item_template_archive/ship_R_phoenix.png?raw=true) `ship_R_phoenix`

![](screenshots/item_template_archive/ship_E_queenelizabeth.png?raw=true) `ship_E_queenelizabeth`

![](screenshots/item_template_archive/ship_SSR_jeanne.png?raw=true) `ship_SSR_jeanne`

#### Equipment blueprints
Equipment bps are the most tedious.

##### AA / guns
Generally, we identify that it's an anti-aircraft weapon (`aa`), or what type of gun it is (`dd/cl/ca/cb/bb`), followed by the number of guns (single, double, triple, quad), and the caliber. If there are multiple guns that share a caliber, then add some other identifying information.

Examples:

![](screenshots/item_template_archive/bp_aa_hazermeyer_T0.png?raw=true) `bp_aa_hazermeyer_T0`

![](screenshots/item_template_archive/bp_ca_triple203mk09_T3.png?raw=true) `bp_ca_triple203mk09_T3`

![](screenshots/item_template_archive/bp_ca_triple203mk15_T3.png?raw=true) `bp_ca_triple203mk15_T3`

You might be thinking that this is way too much effort to document gun blueprints that literally no one cares about, and you'd be right. This does happen to guns that you DO care about:

![](screenshots/item_template_archive/bp_dd_single138_T3.png?raw=true) `bp_dd_single138_T3`

![](screenshots/item_template_archive/bp_dd_single138_1927_T123.png?raw=true) `bp_dd_single138_1927_T123.png`

In this case I added the modifier to the gun no one cares about, since the single138 is rather iconic, but this is all arbitrary. Also the latter gun's template happens to have no rarity-identifying-information, so it's all blobbed together, but since no one cares about that gun it's probably fine.


##### Planes
We use `cvF`, `cvD`, and `cvT` to denote fighters, dive bombers, and torpedo bombers.
![](screenshots/item_template_archive/bp_cvF_corsair_T2.png?raw=true) `bp_cvF_corsair_T2`

![](screenshots/item_template_archive/bp_cvD_helldiver_T3.png?raw=true) `bp_cvD_helldiver_T3`

![](screenshots/item_template_archive/bp_cvT_barracuda_T2.png?raw=true) `bp_cvT_barracuda_T2`
##### Torps
Self-explanatory
![](screenshots/item_template_archive/bp_torp_quint533_T2.png?raw=true) `bp_torp_quint533_T2`

##### Aux
Generally self-explanatory.
![](screenshots/item_template_archive/bp_aux_repairbox_T3.png?raw=true) `bp_aux_repairbox_T3`
