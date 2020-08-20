[English Quick Guide](doc%2FQuick_guide.md) 

[Download Easy Install-v2](https://github.com/whoamikyo/AzurLaneAutoScript/releases)

**| English | [Chinese](README.md) |**

# AzurLaneAutoScript

Alas, an Azur Lane automation tool with GUI (For CN server, can support other server).

![gui](doc/README.assets/gui_en.png)

## Features  

- **Campaign**: Support for new maps grows every day, check a `./campaign` folder to see supported maps

- **Events**: Support for new maps grows every day, check a `./campaign` folder to see supported maps

- **Daily Mission**: Able to finish everything in 30 minutes, repeated run will skip over what has been done on that day  

  Daily Mission(Submarine not support).
  
- **Events x3 Bonus**: 30 minutes to finish A1 to B3 in events.

- **Commissions**: Checks commissions at the configured time during campaign, accept commission rewards, research rewards, and daily mission rewards.  

- **Misc Features**  

  Morale Control, Calculate Morale to prevent it from going sad, or to maintain Morale to earn experience.

  HP Monitoring, Low HP Retire, Frontline HP Balancing  

  Equipment Change  
 
  Periodic Screeshot Record  
 
  Auto Retire
  
  Enhance shipfu
 
  Map completion mode, when running new map, it will try to do 3 star clear


## Known issues

Sort by frequency

- **GUI starts slowly, uiautomator2 starts slowly**
- **Unable to deal with network fluctuations** Reconnect popup window
- **The green face, yellow face and red face will be displayed** This is the BUG, Alas will restart the game every 2 hour to update the affections level.
- **Exercises may fail**
- **Screen swipe will not work in rare circumstances**
