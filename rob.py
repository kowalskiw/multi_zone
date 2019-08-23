with open('D:\CR_qsync\ED_\ '[:-1]+'02_cfd\ '[:-1]+'2019\ '[:-1] +'48_aflofarm_pabianice\ '[:-1] + '02_ozone\el3D.json') as file:
    tab = file.readlines()

for j in [14, 733, 1453, 2173, 2893, 3613, 4333, 5053, 5773, 6493]:
    for i in [40, 64, 88, 112, 134, 156, 178, 200, 222, 244, 266, 288, 310, 332, 354, 376, 398, 442, 464, 486, 508, 530,
              552, 574, 596, 618, 640, 664, 688, 712]:
        tab[i+j-14] = '            {"b":0,\n'

# index = 15
# bugs = 0
# for i in tab[index:7213]:
#     splitedi = i.split('"')
#     print(splitedi)
#     try:
#         if splitedi[0] == '        ':
#             tab[index+1] = '        {\n'
#     except:
#         print('bug')
#         bugs += 1
#         index +=1
#         continue
#     index += 1
# print(bugs)

# index = 1451
# bugs = 0
#     for i in tab[index:2172]:
#     splitedi = i.split(':')
#     print(splitedi)
#     try:
#         if splitedi[1] == "2,\n":
#             tab[index] = splitedi[0] + ':6,\n'
#         elif splitedi[1] == '2},\n':
#             tab[index] = splitedi[0] + ':6},\n'
#         elif splitedi[1] == '2}\n':
#             tab[index] = splitedi[0] + ':6}\n'
#     except:
#         print('bug')
#         bugs += 1
#         index +=1
#         continue
#     index += 1
#
# index = 4332
# bugs = 0
# for i in tab[index:7212]:
#     splitedi = i.split(':')
#     print(splitedi)
#     try:
#         if splitedi[1] == "2,\n":
#             tab[index] = splitedi[0] + ':10,\n'
#         elif splitedi[1] == '2},\n':
#             tab[index] = splitedi[0] + ':10},\n'
#         elif splitedi[1] == '2}\n':
#             tab[index] = splitedi[0] + ':10}\n'
#     except:
#         print('bug')
#         bugs += 1
#         index +=1
#         continue
#     index += 1
#
# print(bugs)
#
# rem0 = '            {"beam":0,\n'
# rem1 = '            {"beam":-1,\n'
#
# i = 0
# while rem0 in tab:
#     tab.remove(rem0)
#     i += 1
# print(i)
#
# while rem1 in tab:
#     tab.remove(rem1)
#     i += 1
# print(i)
#
# print(tab)
#
# for i in range(20):
#     tab.insert(6910 + 20 * i, '            {\n')
#
# for i in range(len(tab)):
#     if len(tab[i]) == 16 or len(tab[i]) == 17:
#         print(i)
#         tab.insert(i+1, '            {\n')
#
# print(tab)

with open('D:\CR_qsync\ED_\ '[:-1]+'02_cfd\ '[:-1]+'2019\ '[:-1] +'48_aflofarm_pabianice\ '[:-1] + '02_ozone\el3Da.json', 'w') as file:
    file.writelines(tab)
