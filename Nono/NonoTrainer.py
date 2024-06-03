import asyncio
import discord
import numpy as np
import os
import settings
import sys
import time
from constrainedSum import constrained_sum_pos, constrained_sum_sample

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
Message = discord.Message
  
@client.event
async def on_ready() -> None:
    print('Wassup. What shall we do today?'.format(client))

@client.event
async def end_session(input: str) -> None:
  commands = ["abort","stop","$pattern","$help","trainer"]
  if input.content in commands:
    await input.channel.send("Session ends. Type new command to start new session.")
    python = sys.executable
    os.execl(python, python, * sys.argv)

@client.event 
async def ask_question(message: Message, question: str, ans_list: list) -> str:
  # Use to ask question and check then returns the answer if it is valid (in ans_list) otherwise the loop continues
  def check(msg):
    return msg.author == message.author
  
  await message.channel.send(question)
  # loop checking whether the messages are in the correct format
  while True:
    ans = await client.wait_for("message", check=check)
    await end_session(ans)
    if ans.content in ans_list:
        return ans.content

@client.event
async def ask_pattern(message: Message) -> str:
  tile_size = str(np.arange(5,26))
  number_size = str([np.arange(1,14)]+['all'])
  
  tile_select = "How many tiles we doing, fellas? (5-25)"
  tile = await ask_question(message, tile_select, tile_size)
  
  number_select = f"{tile} tiles. And how many numbers? (1-{int(np.ceil(int(tile.content)/2))} or 'all')"
  number = await ask_question(message, number_select, number_size)

  return tile, number

@client.event
async def ask_trainer(message: Message) -> str:
  modes = ['gamemode 1', 'gamemode 2']
  tile_size = str(np.arange(5,101))
  second_size = str(np.arange(0,101.1))
  
  gamemode_select = "What gamemode do you wish to play? (random='gamemode 1', limited='gamemode 2')"
  gamemode = await ask_question(message, gamemode_select, modes)
  
  tile_select = f"Chosen {gamemode}. How many tiles we doing, fellas? (5-100)"
  tile = await ask_question(message, tile_select, tile_size)
  
  second_select = f"{tile} tiles, huh?. And how many seconds do you need? (<=100)"
  second = await ask_question(message, second_select, second_size)
  await message.channel.send(f"So you need {second} seconds. Well, good luck!")
  
  return tile, second, gamemode

@client.event
async def congratulate(gamemode,pattern_all,pattern_add,total_time,second,message: Message):
  #This function is only used when user answer the questions correctly. This function will send the text message and also check for remaining patterns when playing gamemode 2
  
  sentence = "Correct! You made it in time. I knew you can do it." if (total_time <= second) else "Good. But you went over the time limit. I suggest getting good."
  
  if gamemode == 'gamemode 1':
    await message.channel.send(f"{sentence} Time: %.4s seconds \n" % (total_time))

  elif gamemode == 'gamemode 2':
    pattern_remaining = (len(pattern_all))-(len(pattern_add))
    if pattern_remaining != 0:
      await message.channel.send(f"{sentence}  Time: %.4s seconds \n**{pattern_remaining}** perfect patterns remaining." % (total_time))

    elif pattern_remaining == 0:
      await message.channel.send(f"**Congratulations!** Game ended. There are no perfect patterns left in the pool.")
      await message.channel.send(file=discord.File('cat_close_up.png'))
      python = sys.executable
      os.execl(python, python, * sys.argv)

@client.event
async def nono_pattern(tile,number,message):
  pattern_pos = []
  if number == "all":
    await message.channel.send(f"**Here are the list of all possible perfect patterns for {tile} tiles**")
    amount = 1
    mine_remaining = int(tile)
    for j in range(int(np.ceil(int(tile)/2))):
      results = constrained_sum_pos(amount, mine_remaining)
      pattern_pos.append(results)
      await message.channel.send(f"The perfect patterns with **{amount}** numbers are \n{sorted(pattern_pos[j])}")
      amount +=1
      mine_remaining -= 1
      await asyncio.sleep(1)
  
  else: 
    amount = int(number)
    mine_remaining = int(tile)+1-amount
    results = constrained_sum_pos(amount, mine_remaining)
    pattern_pos.append(results)
    await message.channel.send(f"The perfect patterns with **{amount}** numbers for {tile} tiles are")
    await message.channel.send(f"{sorted(pattern_pos[0])}\n")
    
  await message.channel.send(f"Totaling to **{sum(len(l) for l in pattern_pos)}** unique combinations")
  
@client.event
async def nono_trainer(tile,second,gamemode,message: Message):
  YES = ["y","yy","ye","yes","yea","yeah","Y","Ye","Yes","YES","Yea","Yeah",]
  NO = ["n","nn","no","nah","na","nein","nope","N","No","NO","Nah","Na","Nein","Nope"]
  tile_number = int(tile)
  second_float = float(second)
  pattern_all = []
  pattern_add = []
  result_wrong = []
  
  if gamemode == 'gamemode 2':
    amount_2 = 1
    mine_remaining_2 = int(tile)
    for j in range(int(np.ceil(int(tile)/2))):
      patterns = constrained_sum_pos(amount_2, mine_remaining_2)
      pattern_all += patterns
      amount_2 +=1
      mine_remaining_2 -= 1
    
  while True:
    tiles = tile_number - np.random.randint(2)
    amount = np.random.randint(1,np.ceil(tiles/2)+1)
    mine_remaining = tiles+1-amount

    if gamemode == 'gamemode 1':
      result_1 = constrained_sum_sample(amount, mine_remaining)
      
    elif gamemode == 'gamemode 2':
      result_1 = constrained_sum_sample(amount, mine_remaining)
      while True:
        if (sorted(result_1) in pattern_add) or (sorted(result_1) in result_wrong):
          tiles = tile_number - np.random.randint(2)
          amount = np.random.randint(1,np.ceil(tiles/2)+1)
          mine_remaining = tiles+1-amount
          result_1 = constrained_sum_sample(amount, mine_remaining)
        elif (sorted(result_1) not in pattern_add) and (sorted(result_1) not in result_wrong):
          break
      
    start_time = time.time()    
    await message.channel.send(f"Is **{result_1}** a perfect pattern for {tile} tiles?(y/n)")

    #loop checking whether the messages are in the correct format
    while True: 
      answer = await client.wait_for("message")
      await end_session(answer)
      if ((answer.content in YES)&(tile_number == tiles))|((answer.content in NO)&(tile_number != tiles)):
        end_time = time.time()-0.5
        await asyncio.sleep(0.5)
        
        if (sorted(result_1) in sorted(pattern_all)) and (sorted(result_1) not in pattern_add):
          pattern_add += [sorted(result_1)]
        if (sorted(result_1) not in sorted(pattern_all)) and (sorted(result_1) not in result_wrong):
          result_wrong += [sorted(result_1)]
          
        await congratulate(gamemode,pattern_all,pattern_add,end_time-start_time,second_float,message)
        await asyncio.sleep(0.5)
        break
      
      elif ((answer.content in YES)&(tile_number != tiles))|((answer.content in NO)&(tile_number == tiles)):
        end_time = time.time()-0.5
        await asyncio.sleep(0.5)
        if end_time-start_time <= second_float:
          await message.channel.send("Wrong. But you answered within the time limit. I respect the effort.")
          await asyncio.sleep(0.5)
          break
        if end_time-start_time > second_float:
          await message.channel.send("Wrong answer and went over the time limit as well??? Major skill issues brotha.")
          await asyncio.sleep(0.5)
          break
      else:
        continue
      #else: 
        #await asyncio.sleep(0.5)
        #await message.channel.send("What did you just typed? (y/n) existed for a reason. you know? I'll ask again.")
        #continue

@client.event
async def on_message(message):
  if message.author == client.user:
      return
      
  if message.content.startswith('ABORT'):
      await message.channel.send('Session ends. Type new commands to start new session.',delete_after=0)
      time.sleep(20)
      return

  if  message.content.startswith('$help'):
    await asyncio.sleep(0.5)
    embed = discord.Embed(
      colour=discord.Colour.teal(),
      title="Commands",
      description="Here are the list of commands."
      )
    embed.add_field(name="",value="**$help**  - show list of commands \n**$pattern**  - show all possible perfect patterns in x amount of tiles \n**$trainer**  - train your perfect patterns ")
    await message.channel.send(embed=embed)
    
  if  message.content.startswith('$pattern'):
    await asyncio.sleep(0.5)
    embed = discord.Embed(
      colour=discord.Colour.teal(),
      title="Perfect Patterns List",
      description="Perfect pattern is a pattern that can solve the entire row/column."
      )
    embed.add_field(name="References for nonosweeper grid sizes",value="Beginner      = 6 tiles \nIntermediate  = 10 tiles \nExpert width  = 12 tiles \nExpert height = 15 tiles \nGenius width  = 15 tiles \nGenius height = 20 tiles")
    await message.channel.send(embed=embed)
    tile,number = await ask_pattern(message)
    await nono_pattern(tile,number,message)
    
  if  message.content.startswith('$trainer'):
    await asyncio.sleep(0.5)
    embed = discord.Embed(
      colour=discord.Colour.teal(),
      title="Pattern Trainer",
      description="Perfect pattern trainer for Nonograms and Nonosweeper. Type 'stop' to stop the session. \nNote: Perfect pattern is a pattern that can solve the entire row/column."
      )
    embed.add_field(name="Gamemode",value="Gamemode 1 = Random patterns. A same combination may appear again. Game ended when ever player choose to. \nGamemode 2 = Choose perfect patterns from the pool. Combinations that have already appeared will never appear again. Game ended once it ran out of patterns")
    embed.add_field(name="References for nonosweeper grid sizes",value="Beginner      = 6 tiles \nIntermediate  = 10 tiles \nExpert width  = 12 tiles \nExpert height = 15 tiles \nGenius width  = 15 tiles \nGenius height = 20 tiles")
    await message.channel.send(embed=embed)
    tile,second,gamemode = await ask_trainer(message)
    await nono_trainer(tile,second,gamemode,message)

def main() -> None:
  client.run(settings.DISCORD_SECRET)
  
if __name__ == '__main__':
  main()