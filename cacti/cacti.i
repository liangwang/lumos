%module cacti
%include<std_string.i>
%include<std_deque.i>
%include<std_list.i>
%include<std_map.i>
%include<std_pair.i>
%include<std_set.i>
%include<std_vector.i>

%include "exception.i"

%exception {
  try {
        $action
          } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
 }


%rename(cxxop_add) operator +;
%rename(cxxop_assign) operator =;

%{
/* Includes the header in the wrapper code */
#include "cacti_interface.h"
%}

/* Parse the header file to generate wrappers */
%include "cacti_interface.h"
