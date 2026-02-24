d = {'players': {'france': {
                                    'player_index': 1, 
                                    'available_units': 2
                                    }, 
                 'germany': {
                                    'player_index': 2, 
                                    'available_units': 3
                                                } }}


for player_name in d['players']:
    for index in d['players'][player_name].values():
        print(index)
        if index == 2:
            player = player_name
            
print(player_name)