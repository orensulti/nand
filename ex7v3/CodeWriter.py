# Constants which are relevant to the CodeWriter class
LABEL_BEGIN = '('
LABEL_END = ')'
SP_START_ADDRESS = '256'
ARITHMETIC = 0
PUSH = 1
POP = 2
LCL = 'local'
ARG = 'argument'
THIS = 'this'
THAT = 'that'
PTR = 'pointer'
TEMP = 'temp'
CONST = 'constant'
STATIC = 'static'

TRUE = '-1'
FALSE = '0'


class CodeWriter:
    """The CodeWriter class Translates VM commands into Hack assembly code. """
    def __init__(self, asm_file):

        # first, initialization of dictionaries which will be used by this class
        # arithmetic operations:
        self._arithmetic_name = dict()
        self._arithmetic_name.update({'add': '+', 'sub': '-', 'or': '|', 'and': '&',
                                      'neg': '-', 'not': '!', 'eq': 'JEQ', 'gt': 'JGT',
                                      'lt': 'JLT'})
        # commands:
        self._command_type = dict()
        self._command_type.update({'ARITHMETIC': 0, 'PUSH': 1, 'POP': 2})

        # command type-name mapping:
        self._command_mapping = dict()
        self._command_mapping.update({'add': 'ARITHMETIC', 'sub': 'ARITHMETIC',
                                      'neg': 'ARITHMETIC', 'eq': 'ARITHMETIC',
                                      'gt': 'ARITHMETIC', 'lt': 'ARITHMETIC',
                                      'and': 'ARITHMETIC', 'or': 'ARITHMETIC',
                                      'not': 'ARITHMETIC', 'push': 'PUSH',
                                      'pop': 'POP'})
        # segments
        self._segment = dict()
        self._segment.update({'local': 'LCL', 'argument': 'ARG', 'this': 'THIS',
                              'that': 'THAT', 'pointer': 'PTR', 'temp': 'TEMP',
                              'constant': 'CONST', 'static': 'STATIC'})

        # registers
        self._register = dict()
        self._register.update({'SP': 'R0', 'local': 'R1', 'argument': 'R2',
                               'pointer': 'R3', 'this': 'R3', 'that': 'R4',
                               'temp': 'R5', 'REG_COPY': 'R13'})

        # prepare the output asm file to be ready to be written
        self._asm_file = open(asm_file, 'w')

        # list which will hold the lines in the output asm file
        self._asm_lines = []

        # we save the number of the label we will generate so it will makes the labels
        # with different names.
        self._label_num = 0

        self._file_name = ""

        # initialize the Stack pointer to start from 256
        self.init_sp()

    def get_command_mapping_dict(self):
        """
        Getter method for the command mapping dict
        """
        return self._command_mapping

    def get_command_type_dict(self):
        """
        Getter method for the command type dict
        """
        return self._command_type

    def init_sp(self):
        """
        This method is responsible to initialize RAM[0] with SP_START_ADDRESS (= 256)
        """
        self.append_address(SP_START_ADDRESS)
        self.change('D', 'A')
        self.append_address(self._register.get('SP'))
        self.change('M', 'D')

    def write_arithmetic(self, command):
        """
        This Method is responsible to translate given arithmetic command to the asm
        suitable command.
        :param command: command
        """
        # extract the correct operation according to the arithmetic from the dictionary
        # (for example add is "+")
        operation = self._arithmetic_name.get(command)

        if command == 'add' or command == 'sub' or command == 'or' or command == 'and':
            self.dec_sp()
            self.pop('D')
            self.peek('A')
            self.change('D', 'A' + operation + 'D')
            self.push('D')
        elif command == 'neg' or command == 'not':
            self.dec_sp()
            self.peek('D')
            self.change('D', operation + 'D')
            self.push('D')
        elif command == 'lt' or command == 'gt':
            self.dec_sp()
            self.peek('D')

            # if the stack head is positive
            self.append_jump_to_label("positive" + "_label" +
                                      str(self._label_num), 'JGT')

            # the stack head is negative
            self.dec_sp()
            self.append_address(self._register.get('REG_COPY'))
            self.change('M', 'D')
            self.peek('D')

            # if the second number from stack head is negative
            self.append_jump_to_label("same_sign" + "_label" + str(self._label_num),
                                      'JLT')

            # the second number from stack head is positive so jump
            self.append_jump("diff_sign_stack_top_neg_second_pos" + "_label" +
                             str(self._label_num))

            # the stack head is positive, we want to check the second number
            self.append_label("positive" + "_label" + str(self._label_num))
            self.dec_sp()
            self.append_address(self._register.get('REG_COPY'))
            self.change('M', 'D')
            self.peek('D')

            # the stack head is positive if the second number is positive
            self.append_jump_to_label("same_sign" + "_label" + str(self._label_num),
                                      'JGT')

            # the stack head is positive second number from stack head is negative
            self.append_jump("diff_sign_stack_top_pos_second_neg" + "_label" +
                             str(self._label_num))

            # the stack head is positive second number from stack head is positive
            self.append_label("same_sign" + "_label" + str(self._label_num))
            self.append_address(self._register.get('REG_COPY'))
            self.change('A', 'M')
            self.change('D', 'D-A')
            self.base_handle(command)

            # jump to continue program
            self.append_jump("continue" + "_label" + str(self._label_num))

            # the stack head is positive anf the second number is negative
            self.append_label("diff_sign_stack_top_pos_second_neg" + "_label" +
                              str(self._label_num))
            if command == 'lt':
                self.push('-1')
            if command == 'gt':
                self.push(FALSE)
            # continue program
            self.append_jump("continue" + "_label" + str(self._label_num))

            # the stack head is negative the second number is positive
            self.append_label("diff_sign_stack_top_neg_second_pos" + "_label" +
                              str(self._label_num))
            if command == 'lt':
                self.push(FALSE)
            if command == 'gt':
                self.push(TRUE)

            # continue program
            self.append_label("continue" + "_label" + str(self._label_num))
            self._label_num += 1

        elif command == 'eq':
            self.dec_sp()
            self.pop('D')
            self.peek('A')
            self.change('D', 'A-D')
            self.base_handle(command)

            self.append_label("continue" + "_label" + str(self._label_num))
            self._label_num += 1

        else:
            print("Invalid Arithmetic command")

    def base_handle(self, command):
        """
        Basic handle when no overflow can occur (we are safe if both numbers have
        the same sign - both positive or negative)
        :param command: The arithmetic command
        """
        operation = self._arithmetic_name.get(command)

        # its important to add the _label_num to the label name, otherwise, if we
        # have several eq_label for example, it will jump to the last of them which
        # will be a bug!

        label = "_label" + str(self._label_num)

        # vm represents true as -1 (minus one, 0xFFFF) and false as  0 (zero, 0x0000)
        self.append_jump_to_label(command + label, operation)
        self.push(FALSE)

        self.append_jump("continue" + "_label" + str(self._label_num))
        self.append_label(command + label)
        self.push(TRUE)

    def append_label(self, label_name):
        """ Adds to the asm_lines list a line of label declaration (Label_name)
            :param label_name: the name of the label
        """
        self._asm_lines.append(LABEL_BEGIN + label_name + LABEL_END)

    def append_conditional_jump(self, input_to_jump_command, condition):

        """ Adds to the asm_lines list a line of jump to label
            :param input_to_jump_command:
            :param condition: condition of the jump for example JEQ
        """
        self._asm_lines.append(input_to_jump_command + ";" + condition)

    def append_jump(self, label_name):
        """ Adds to the asm_lines list the two lines of jump without condition to label
            :param label_name: name of the label we enforce jump to
        """
        self.append_address(label_name)
        self._asm_lines.append('0;JMP')

    def append_jump_to_label(self, label_name, condition):
        """ Adds to the asm_lines list the two lines of jump with a condition
            :param label_name: name of the label we want to jump to
            :param condition: condition of the jump for example JEQ
        """
        self.append_address(label_name)
        self.append_conditional_jump('D', condition)

    def calc_segment_pointer_plus_offset_address(self, segment, index, register):
        """
        This method puts in A the address of segmentPointer + index
        :param segment: the name of the segment from the line in the vm file
        :param index: the numerical part of the command
        :param register: A or D (address or data)
        """
        # A = address = segmentPointer + i
        self.append_address(index)
        self.change('D', 'A')
        self.append_address(segment)
        self.change('A', '' + register + '+D')

    def push_constant_segment(self, index):
        """
        This method do the following: *SP=index
        :param index: the numerical part of constant command
        """
        self.append_address(index)
        self.change('D', 'A')
        self.push('D')

    def push_register_or_memory_segment(self, segment, index, register):
        """
        This method is responsible to translate push segment i
        segment can be one of the following: LCL,AEG,THIS,THAT,TEMP,PTR
        :param segment: the name of the segment from the line in vm file
        :param index: the numerical part of the command
        :param register: A or D
        """
        self.calc_segment_pointer_plus_offset_address(segment, index, register)
        self.change('D', 'M')
        # D = *(segmentPointer + i) = *addr
        # *SP = *addr, SP++
        self.push('D')

    def pop_register_or_memory_segment(self, segment, index, register):
        """
        This method is responsible to translate pop segment i
        segment can be one of the following:  LCL,AEG,THIS,THAT,TEMP,PTR
        :param segment: the name of the segment from the line in vm file
        :param index: the numerical part of the command
        :param register: A or D
        """
        # *R13=addr=segmentPointer+i
        self.calc_segment_pointer_plus_offset_address(segment, index, register)
        self.change('D', 'A')
        self.append_address(self._register.get('REG_COPY'))
        self.change('M', 'D')
        # D=*SP, SP--
        self.dec_sp()
        self.peek('D')
        # A=addr
        self.append_address(self._register.get('REG_COPY'))
        self.change('A', 'M')
        # *addr = D = *SP
        self.change('M', 'D')

    def pop_static_segment(self, label):
        """
         This method is responsible to translate pop segment i
        segment of static
        :param label: the label of the static variable
        """
        # D=*SP
        self.dec_sp()
        self.peek('D')

        self.append_address(label)
        self.change('M', 'D')

    def push_static_segment(self, label):
        """
        This method is responsible to translate push segment i
        segment of static
        :param label: the label of the static variable
        """
        self.append_address(label)
        self.change('D', 'M')
        self.push('D')

    def set_file_name(self, file_name):
        """
        set the file name
        :param file_name: tha name of the file we need to translate
        :return: the name of the file
        """
        self._file_name = file_name

    def create_static_label(self, index):
        """
        This method creates the label of the static variable.
        the label consists of the file name (without it's type) dot the index of the
        static variable.
        :param index: the static number at the vm command
        :return: the label we create
        """
        file_name = self._file_name.split(".")[0]
        return str(file_name) + "." + str(index)

    def write_push_pop(self, command, segment, index):
        """
        Writes the assembly code that is the translation of the given command, where
        command is either C_PUSH or C_POP.
        :param command:
        :param segment:
        :param index:
        :return:
        """
        if command == PUSH:
            # it's a PUSH command,
            # check if the segment is memory segment(LCL,ARG,THIS,THAT) or
            # register segment(TEMP,POINTER) or
            # CONSTANT segment
            # STATIC
            if segment == CONST:
                self.push_constant_segment(index)
            elif segment in (LCL, ARG, THIS, THAT):
                self.push_register_or_memory_segment(self._segment.get(segment), index,
                                                     'M')
            elif segment in (TEMP, PTR):
                self.push_register_or_memory_segment(self._register.get(segment), index,
                                                     'A')
            elif segment == STATIC:
                self.push_static_segment(self.create_static_label(index))
            else:
                print("Unsuitable segment")
        elif command == POP:
            # it's a POP command,
            # check if the segment is memory segment(LCL,ARG,THIS,THAT) or
            # register segment(TEMP,POINTER) or
            # CONSTANT segment
            # STATIC
            if segment in (LCL, ARG, THIS, THAT):
                self.pop_register_or_memory_segment(self._segment.get(segment), index,
                                                    'M')
            elif segment in (TEMP, PTR):
                self._register.get(segment)
                self.pop_register_or_memory_segment(self._register.get(segment),
                                                    index, 'A')
            elif segment == STATIC:
                self.pop_static_segment(self.create_static_label(index))
            else:
                print("Unsuitable segment")

        else:
            print("Invalid command")

    def append_address(self, address):
        """
        Writes into the output asm file A command (@+address)
        :param address: the address to point to
        """
        self._asm_lines.append('@' + address)

    def change(self, dest, comp):
        """ Writes into the asm_lines list the comp command(dest=comp)
        :param dest:
        :param comp:
        """
        self._asm_lines.append(dest + '=' + comp)

    def write_output_asm_file(self):
        """ This method is responsible to write the asm_list into the output file
        """
        for item in self._asm_lines:
            self._asm_file.write("{}\n".format(item))
        # close the output file
        self.close()

    def close(self):
        """ close the output file """
        self._asm_file.close()

    def inc_sp(self):
        """ Increase the SP in order to access the item in top of the stack by the
        following asm command: @SP M=M+1
        """
        self.append_address('SP')
        self.change('M', 'M+1')

    def dec_sp(self):
        """ Decrease the SP in order to access the item in top of the stack by the
        following asm command: @SP M=M-1
        """
        self.append_address('SP')
        self.change('M', 'M-1')

    def peek(self, dest):
        """ This method implements the peek from stack functionality(in peek we dont
        decrease the SP like in pop). peek will do the following: dest=*SP, by the
        following asm commands:
        @SP
        A=M
        dest=M
        :param dest: dest part(D for example)
        """
        self.append_address('SP')
        self.change('A', 'M')
        self.change(dest, 'M')

    def pop(self, dest):
        """ Pop is like peek but also remove the item in the top of the stack by decrease
        the SP
        :param dest: the dest part
        """
        self.peek(dest)
        self.dec_sp()

    def push(self, comp):
        """ This method implements the push into stack functionality. push will do the
        following: *SP=comp @SP++
        by the following rows of asm:
        @SP
        A=M
        M=comp(for example D)
        @SP
        M=M+1
        :param comp: the comp part
        """
        self.append_address('SP')
        self.change('A', 'M')
        self.change('M', comp)
        self.inc_sp()

    def print_asm_lines(self):
        """
        Method for the convenience of the programmer - to print the asm lines so far.
        """
        for line in self._asm_lines:
            print(line)