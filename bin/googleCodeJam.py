



def check(index, number, one , cha, repl):
    if(index == len(number)-1):
        return number
    
    
    if number[index] != cha:
        one = 0
    if index > 0:
        if(number[ index ] == number[ index -1] ):
            repl += 1

    if( int(number[ index ])  > int(number[ index + 1 ]) ):        
        if(one != 1 or len(number) == 2):
            temp1 = 10**(len(number)-(index+1-repl))
            temp2 = int(number)
            temp1 = (temp2 % temp1) + 1
            temp2 = temp2 - temp1
            return temp2
        else:
            if(len(number) - 2) : 
                temp1 = 10**(len(number) - 1)
                temp2 = int(number)
                temp1 = (temp2 % temp1) + 1
                temp2 = temp2 - temp1
                return temp2
    index += 1
    return check(index, number, one, cha, repl)

if __name__ == '__main__':
    num = input()
    num = int(num)
    listNum = []

    for i in range(num):
        listNum.append(input())

    j  = 1
    for i in listNum:
        print("Case #" + str(j) + ": " + str(check(0, i, 1, i[0],0)))
        j += 1

    








