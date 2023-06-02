from decimal import Decimal

def shift_svg_values(old_d, shift_value):

    def is_int(the_char):

        try:

            int(the_char)
            return True
        
        except:

            return False
        
    def update_number(number_text, shift_value=shift_value):

        if number_text == '':

            return ''
        
        return str(Decimal(number_text) + shift_value)


    old_d_length_after_enumerate = len(old_d) - 1
    new_d = ''
    number_text = ''

    for count, layer_1_pointer in enumerate(old_d):

        #if currently not number/fullstop, skip
        if is_int(layer_1_pointer) is True or layer_1_pointer == '.':

            #start/resume the formation of number
            number_text += layer_1_pointer

            #edge case for last char of old_d not being a valid breakpoint
            if count == old_d_length_after_enumerate:

                new_d += update_number(number_text)

        else:

            #reached breakpoint, i.e. letter or coma

            #if letter is 'C', i.e. curve, we have to multiply the shift value
            new_d += update_number(number_text)
            
            #done with number, reset
            number_text = ''

            #since this breakpoint is "after" our number_text is formed, we add it after number_text
            new_d += layer_1_pointer

    return new_d
