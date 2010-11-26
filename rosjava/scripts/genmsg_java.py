#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import roslib; roslib.load_manifest('rosjava')

import sys
import os
import traceback

import roslib.msgs 
import roslib.packages
import roslib.gentools

from cStringIO import StringIO

MSG_TYPE_TO_JAVA = {'bool': 'boolean',
                    'char': 'char',
                    'byte': 'short',
                    'uint8': 'short', 'int8': 'byte', 
                    'uint16': 'int', 'int16': 'short', 
                    'uint32': 'long', 'int32': 'int',
                    'uint64': 'long', 'int64': 'long',
                    'float32': 'float',
                    'float64': 'double',
                    'string': 'java.lang.String',
                    'time': 'ros.communication.Time',
                    'duration': 'ros.communication.Duration'}

MSG_TYPE_TO_SERIALIZATION_CODE = {
    'bool': '%(buffer)s.put((byte)(%(name)s ? 1 : 0))',
    'char': '%(buffer)s.put((byte)%(name)s)',
    'byte': '%(buffer)s.put((byte)%(name)s)',
    'uint8': '%(buffer)s.put((byte)%(name)s)',
    'int8': '%(buffer)s.put(%(name)s)',
    'uint16': '%(buffer)s.putShort((short)%(name)s)',
    'int16': '%(buffer)s.putShort(%(name)s)',
    'uint32': '%(buffer)s.putInt((int)%(name)s)',
    'int32': '%(buffer)s.putInt(%(name)s)',
    'uint64': '%(buffer)s.putLong(%(name)s)',
    'int64': '%(buffer)s.putLong(%(name)s)',
    'float32': '%(buffer)s.putFloat(%(name)s)',
    'float64': '%(buffer)s.putDouble(%(name)s)',
    'string': 'Serialization.writeString(%(buffer)s, %(name)s)',
    'time': 'Serialization.writeTime(%(buffer)s, %(name)s)',
    'duration': 'Serialization.writeDuration(%(buffer)s, %(name)s)'}

MSG_TYPE_TO_DESERIALIZATION_CODE = {
    'bool': '%s.get() != 0 ? true : false',
    'char': '(char)(%s.get() & 0xff)',
    'byte': '(short)(%s.get() & 0xff)',
    'uint8': '(short)(%s.get() & 0xff)',
    'int8': '%s.get()',
    'uint16': '(int)(%s.getShort() & 0xffff)',
    'int16': '%s.getShort()',
    'uint32': '(long)(%s.getInt() & 0xffffffff)',
    'int32': '%s.getInt()',
    'uint64': '%s.getLong()',
    'int64': '%s.getLong()',
    'float32': '%s.getFloat()',
    'float64': '%s.getDouble()',
    'string': 'Serialization.readString(%s)',
    'time': 'Serialization.readTime(%s)',
    'duration': 'Serialization.readDuration(%s)'}

BUILTIN_TYPE_SIZES = {'bool': 1, 'int8': 1, 'byte': 1, 'int16': 2, 'int32': 4, 'int64': 8,
                      'char': 1, 'uint8': 1, 'uint16': 2, 'uint32': 4, 'uint64': 8,
                      'float32': 4, 'float64': 8, 'time': 8, 'duration': 8}

BOXED_TYPES = {'byte': 'java.lang.Byte',
               'short': 'java.lang.Short',
               'int': 'java.lang.Integer',
               'long': 'java.lang.Long',
               'boolean': 'java.lang.Boolean',
               'float': 'java.lang.Float',
               'double': 'java.lang.Double',
               'java.lang.String': 'java.lang.String',
               'ros.communication.Time': 'ros.communication.Time'}

def builtin_type_size(type):
    return BUILTIN_TYPE_SIZES[type.split('[')[0]]

def base_type_to_java(base_type, boxed=False):
    base_type = base_type.split('[')[0]
    if (roslib.msgs.is_builtin(base_type)):
        if boxed:
            java_type = BOXED_TYPES[MSG_TYPE_TO_JAVA[base_type]]
        else:
            java_type = MSG_TYPE_TO_JAVA[base_type]
    elif (len(base_type.split('/')) == 1):
        if (roslib.msgs.is_header_type(base_type)):
            java_type = 'ros.pkg.roslib.msg.Header'
        elif boxed:
            java_type = BOXED_TYPES[MSG_TYPE_TO_JAVA[base_type]]
        else:
            java_type = base_type
    else:
        pkg = base_type.split('/')[0]
        msg = base_type.split('/')[1]
        java_type = 'ros.pkg.%s.msg.%s' % (pkg, msg)
    return java_type

def base_type_serialization_code(type):
    return MSG_TYPE_TO_SERIALIZATION_CODE[type.split('[')[0]]

def base_type_deserialization_code(type):
    return MSG_TYPE_TO_DESERIALIZATION_CODE[type.split('[')[0]]

def type_initializer(type, default_val = None):
    if default_val:
        return ' = %s' % default_val
    elif roslib.msgs.is_builtin(type):
        if type in ['time', 'duration', 'string']:
            return ' = new %s()' % base_type_to_java(type)
        else:
            return ''
    else:
        return ' = new %s()' % base_type_to_java(type)
    
def msg_decl_to_java(field, default_val=None):
    """
    Converts a message type (e.g. uint32, std_msgs/String, etc.) into the Java declaration
    for that type.
    
    @param type: The message type
    @type type: str
    @return: The Java declaration
    @rtype: str
    """
    java_type = base_type_to_java(field.type)

    if type(field).__name__ == 'Field' and field.is_array:
        if field.array_len is None:
            if field.is_builtin and field.type.split('[')[0] != 'string':
                arr_type = BOXED_TYPES[java_type]
            else:
                arr_type = java_type
            return 'java.util.Vector<%s> %s = new java.util.Vector<%s>()' % (arr_type, field.name, arr_type)
        else:
            return '%s[] %s = new %s[%d]' % (java_type, field.name, java_type, field.array_len)
    else:
        return '%(type)s %(name)s%(initializer)s' % {'type': java_type,
                                                     'name': field.name,
                                                     'initializer': type_initializer(field.type, default_val)}
    
def write_begin(s, spec, file):
    """
    Writes the beginning of the header file: a comment saying it's auto-generated and the include guards
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The spec
    @type spec: roslib.msgs.MsgSpec
    @param file: The file this message is being generated for
    @type file: str
    """
    s.write('/* Auto-generated by genmsg_java.py for file %s */\n'%(file))
    s.write('\npackage ros.pkg.%s.msg;\n' % spec.package)
    s.write('\nimport java.nio.ByteBuffer;\n')
    
def write_end(s, spec):
    """
    Writes the end of the header file: the ending of the include guards
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The spec
    @type spec: roslib.msgs.MsgSpec
    """
    pass
    
def write_imports(s, spec):
    """
    Writes the message-specific imports
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec to iterate over
    @type spec: roslib.msgs.MsgSpec
    """
    s.write('\n') 
    
    
def write_class(s, spec):
    """
    Writes the entire message struct: declaration, constructors, members, constants and member functions
    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: roslib.msgs.MsgSpec
    """
    
    msg = spec.short_name
    s.write('public class %s extends ros.communication.Message {\n' % msg)

    write_constant_declarations(s, spec)
    write_members(s, spec)

    write_constructor(s, spec)
    
    gendeps_dict = roslib.gentools.get_dependencies(spec, spec.package, compute_files=False)
    md5sum = roslib.gentools.compute_md5(gendeps_dict)
    full_text = compute_full_text_escaped(gendeps_dict)
    
    write_member_functions(s, spec,
                           MD5Sum=md5sum,
                           DataType='%s/%s'%(spec.package, spec.short_name),
                           MessageDefinition=full_text)
    
    s.write('} // class %s\n'%(msg))

def write_constructor(s, spec):
    s.write("""
  public %s() {
""" % spec.short_name)
    for field in spec.parsed_fields():
        if field.type.split('[')[0] in roslib.msgs.PRIMITIVE_TYPES and  \
                field.type.split('[')[0] != 'string':
            continue
        if field.is_array and field.array_len:
            s.write("""
    for(int __i=0; __i<%(array_len)d; __i++) {
      %(name)s[__i]%(initializer)s;
    }
""" % {'name': field.name, 'type': field.type.split('[')[0],
       'array_len': field.array_len,
       'initializer': type_initializer(field.type.split('[')[0])})
    s.write('  }\n')
            
def write_member(s, field):
    """
    Writes a single member's declaration and type typedef
    
    @param s: The stream to write to
    @type s: stream
    @param type: The member type
    @type type: str
    @param name: The name of the member
    @type name: str
    """
    java_decl = msg_decl_to_java(field)
    s.write('  public %s;\n' % java_decl)

def write_members(s, spec):
    """
    Write all the member declarations
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: roslib.msgs.MsgSpec
    """
    [write_member(s, field) for field in spec.parsed_fields()]
        
def escape_string(str):
    str = str.replace('\\', '\\\\')
    str = str.replace('"', '\\"')
    return str
        
def write_constant_declaration(s, constant):
    """
    Write a constant value as a static member
    
    @param s: The stream to write to
    @type s: stream
    @param constant: The constant
    @type constant: roslib.msgs.Constant
    """
    
    # integral types get their declarations as enums to allow use at compile time
    s.write('  static final %s;\n'% msg_decl_to_java(constant, constant.val))
        
def write_constant_declarations(s, spec):
    """
    Write all the constants from a spec as static members
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: roslib.msgs.MsgSpec
    """
    [write_constant_declaration(s, constant) for constant in spec.constants]
    s.write('\n')
    
def write_clone_methods(s, spec):
    s.write("""
  public %(type)s clone() {
    %(type)s c = new %(type)s();
    c.deserialize(serialize(0));
    return c;
  }
""" % {'type': spec.short_name})
    s.write("""
  public void setTo(ros.communication.Message m) {
    deserialize(m.serialize(0));
  }
""")

def write_serialization_length(s, spec):
    s.write("""
  public int serializationLength() {
    int __l = 0;
""")
    for field in spec.parsed_fields():
        if field.type.split('[')[0] == 'string':
            if field.is_array:
                if field.array_len is None:
                    s.write('    __l += 4;')
                s.write("""
    for(java.lang.String val : %(name)s) {
      __l += 4 + val.length();
    }
""" % {'name': field.name})
            else:
                s.write('    __l += 4 + %s.length();\n' % field.name)

        elif field.is_builtin:
            if field.is_array and field.array_len is None:
                size_expr = '4 + %s.size() * %d' % (field.name, builtin_type_size(field.type))
            elif field.is_array:
                size_expr = '%d' % (int(field.array_len) * builtin_type_size(field.type))
            else:
                size_expr = '%d' % builtin_type_size(field.type)
            s.write('    __l += %s; // %s\n' % (size_expr, field.name))
        elif field.is_array:
            java_type = base_type_to_java(field.base_type)
            if field.array_len is None:
                s.write('    __l += 4;')
            s.write("""
    for(%s val : %s) {
      __l += val.serializationLength();
    }
""" % (java_type, field.name))
        else:
            s.write('    __l += %s.serializationLength();\n' % field.name)
                        
    s.write('    return __l;\n  }\n')

def write_serialization_method(s, spec):
    s.write("""
  public void serialize(ByteBuffer bb, int seq) {
""")
    for field in spec.parsed_fields():
        if field.is_builtin:
            if field.is_array:
                var_type_unboxed = base_type_to_java(field.base_type)
                if field.base_type in ['string', 'time', 'duration']:
                    var_value = 'val'
                else:
                    var_value = 'val.%sValue()' % var_type_unboxed
                if field.array_len is None:
                    s.write('    bb.putInt(%s.size());' % field.name)
                s.write("""
    for(%(type)s val : %(name)s) {
      %(serialization)s;
    }
""" % {'type': base_type_to_java(field.base_type, boxed=True),
       'name': field.name,
       'serialization': base_type_serialization_code(field.type) % {'buffer': 'bb', 'name': var_value}})
            else:
                s.write('    %s;\n' % (base_type_serialization_code(field.type) % {'buffer': 'bb',
                                                                                   'name': field.name}))
        else:
            if field.is_array:
                if field.array_len is None:
                    s.write('    bb.putInt(%s.size());' % field.name)
                s.write("""
    for(%s val : %s) {
      val.serialize(bb, seq);
    }
""" % (base_type_to_java(field.base_type), field.name))
            else:
                s.write('    %s.serialize(bb, seq);\n' % field.name)
    
    s.write('  }\n')

def write_deserialization_method(s, spec):
    s.write("""
  public void deserialize(ByteBuffer bb) {
""")
    for field in spec.parsed_fields():
        java_type = base_type_to_java(field.base_type)
        if field.is_array:
            if field.array_len is None:
                s.write('    int __%s_len = bb.getInt();' % field.name)
                if field.is_builtin:
                    s.write("""
    %(name)s = new java.util.Vector<%(boxed_type)s>(__%(name)s_len);
    %(name)s.setSize(__%(name)s_len);
    for(int __i = 0; __i<__%(name)s_len; __i++) {
      %(name)s.set(__i, %(deserialization_code)s);
    }
""" % {'name': field.name,
       'boxed_type': BOXED_TYPES[java_type],
       'type': java_type,
       'deserialization_code': base_type_deserialization_code(field.type) % 'bb'})
                else:
                    s.write("""
    %(name)s = new java.util.Vector<%(type)s>(__%(name)s_len);
    %(name)s.setSize(__%(name)s_len);
    for(int __i = 0; __i<__%(name)s_len; __i++) {
      %(type)s __tmp = new %(type)s();
      __tmp.deserialize(bb);
      %(name)s.set(__i, __tmp);
    }
""" % {'name': field.name,
       'type': java_type})
            elif field.is_builtin:
                s.write("""
    int __%(name)s_len = %(name)s.length;
    for(int __i = 0; __i<__%(name)s_len; __i++) {
      %(name)s[__i] = %(deserialization_code)s;
    }
""" % {'name': field.name,
       'deserialization_code': base_type_deserialization_code(field.type) % 'bb'})
            else:
                s.write("""
    int __%(name)s_len = %(name)s.length;
    for(int __i = 0; __i<__%(name)s_len; __i++) {
      %(name)s[__i].deserialize(bb);
    }
""" % {'name': field.name})
        elif field.is_builtin:
            s.write('    %s = %s;\n' % (field.name,
                                        base_type_deserialization_code(field.type) % 'bb'))
        else:
            s.write('    %s.deserialize(bb);\n' % field.name)
    s.write('  }\n')
    
def write_serialization_methods(s, spec):
    write_serialization_length(s, spec)
    write_serialization_method(s, spec)
    write_deserialization_method(s, spec)
    
def write_member_functions(s, spec, MD5Sum, DataType, MessageDefinition):
    """
    The the default member functions
    """
    s.write('\n')
    s.write('  public static java.lang.String __s_getDataType() { return "%s"; }\n' % DataType)
    s.write('  public static java.lang.String __s_getMD5Sum() { return "%s"; }\n' % MD5Sum)
    s.write('  public static java.lang.String __s_getMessageDefinition() { return %s; }\n\n' % MessageDefinition)
    s.write('  public java.lang.String getDataType() { return __s_getDataType(); }\n')
    s.write('  public java.lang.String getMD5Sum() { return __s_getMD5Sum(); }\n')
    s.write('  public java.lang.String getMessageDefinition() { return __s_getMessageDefinition(); }\n\n')

    write_clone_methods(s, spec)
    write_serialization_methods(s, spec)
    
def compute_full_text_escaped(gen_deps_dict):
    """
    Same as roslib.gentools.compute_full_text, except that the
    resulting text is escaped to be safe for C++ double quotes

    @param get_deps_dict: dictionary returned by get_dependencies call
    @type  get_deps_dict: dict
    @return: concatenated text for msg/srv file and embedded msg/srv types. Text will be escaped for double quotes
    @rtype: str
    """
    definition = roslib.gentools.compute_full_text(gen_deps_dict)
    lines = definition.split('\n')
    s = StringIO()
    for line in lines:
        line = escape_string(line)
        s.write('\"%s\\n\" +\n'%(line))

    s.write('\"\"')
    val = s.getvalue()
    s.close()
    return val

def generate(msg_path):
    """
    Generate a message
    
    @param msg_path: The path to the .msg file
    @type msg_path: str
    """
    (package_dir, package) = roslib.packages.get_dir_pkg(msg_path)
    (_, spec) = roslib.msgs.load_from_file(msg_path, package)
    
    s = StringIO()
    write_begin(s, spec, msg_path)
    write_imports(s, spec)
    
    write_class(s, spec)
    
    write_end(s, spec)
    
    output_dir = '%s/msg_gen/java/ros/pkg/%s/msg'%(package_dir, package)
    if (not os.path.exists(output_dir)):
        # if we're being run concurrently, the above test can report false but os.makedirs can still fail if
        # another copy just created the directory
        try:
            os.makedirs(output_dir)
        except OSError, e:
            pass
         
    f = open('%s/%s.java'%(output_dir, spec.short_name), 'w')
    print >> f, s.getvalue()
    
    s.close()

def generate_messages(argv):
    for arg in argv[1:]:
        generate(arg)

if __name__ == "__main__":
    generate_messages(sys.argv)
